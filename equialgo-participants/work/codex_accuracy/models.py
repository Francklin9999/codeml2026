"""Independent fitted-model candidates with counterfactual nuisance averaging.

Validation here measures historical committee reproduction, NOT hidden-reference
accuracy. No hidden labels are available. Writes only Codex-owned paths.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, SplineTransformer
from sklearn.pipeline import make_pipeline
from sklearn.compose import ColumnTransformer
from sklearn.metrics import roc_auc_score, log_loss, accuracy_score
from statsmodels.discrete.discrete_model import Probit
from scipy.stats import rankdata

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).parent
OUT=ROOT/'upload_codex'
OUT.mkdir(exist_ok=True)
h=pd.read_csv(ROOT/'data/donnees_demandes.csv')
d=pd.read_csv(ROOT/'data/candidats_evaluation.csv')
def encode(f):
    x=pd.DataFrame({'cote':f.cote_r_equivalent,'hours':f.heures_travail_semaine,
                    'log_income':np.log(f.revenu_familial_estime),
                    'log_distance':np.log1p(f.distance_domicile_campus_km),
                    'firstgen':f.premiere_generation_universitaire})
    return x.join(pd.get_dummies(f[['region_administrative','programme_etudes']],drop_first=True).astype(float))
x=encode(h);t=encode(d).reindex(columns=x.columns,fill_value=0)
y=h.decision_octroi.to_numpy()
a,b=train_test_split(np.arange(len(h)),test_size=.25,stratify=y,random_state=2026)
models={
 'model_A_boosted_academic_hours':HistGradientBoostingClassifier(max_iter=220,max_leaf_nodes=12,
                       min_samples_leaf=70,l2_regularization=12,learning_rate=.06,random_state=42),
 'model_B_spline_academic_hours':make_pipeline(ColumnTransformer([
     ('splines',SplineTransformer(n_knots=4,degree=3),['cote','hours','log_income','log_distance'])],
     remainder='passthrough'),StandardScaler(),LogisticRegression(C=.3,max_iter=2000)),
 'model_C_extra_trees_academic_hours':ExtraTreesClassifier(n_estimators=350,min_samples_leaf=25,
                      max_features=.85,n_jobs=2,random_state=2026),
}
best=pd.read_csv(ROOT/'work/strat3/batch/r2_11.csv').set_index('id_candidat').loc[d.id_candidat].decision_octroi.to_numpy()
records=[]
def save(name,score,description,validation=None):
    pred=np.zeros(len(t),dtype=int)
    pred[np.argsort(-score,kind='stable')[:1600]]=1
    pd.DataFrame({'id_candidat':d.id_candidat,'decision_octroi':pred}).to_csv(OUT/f'{name}.csv',index=False)
    np.save(HERE/f'{name}_scores.npy',score)
    r={'file':f'{name}.csv','description':description,'grants':int(pred.sum()),
       'changed_from_r2_11':int((pred!=best).sum()),'committee_validation':validation}
    records.append(r)
    print(json.dumps(r),flush=True)

# Average over actual observed nuisance profiles, identically for every applicant.
# Only academic score and hours vary across applicants in these three candidates.
profiles=x.sample(n=48,random_state=4242)
for name,model in models.items():
    model.fit(x.iloc[a],y[a]);p=model.predict_proba(x.iloc[b])[:,1]
    val={'auc':float(roc_auc_score(y[b],p)),'log_loss':float(log_loss(y[b],p)),
         'accuracy':float(accuracy_score(y[b],p>=.5))}
    model.fit(x,y)
    score=np.zeros(len(t))
    for _,profile in profiles.iterrows():
        counterfactual=pd.DataFrame(np.tile(profile.to_numpy(),(len(t),1)),columns=x.columns)
        counterfactual['cote']=t.cote.to_numpy()
        counterfactual['hours']=t.hours.to_numpy()
        score+=model.predict_proba(counterfactual)[:,1]/len(profiles)
    save(name,score,'Fitted committee model; average over 48 common nuisance profiles; retain academic score and hours.',val)
    if name.startswith('model_A'):
        # Alternate causal hypothesis: proxy distributions differ by geography.
        # Transport income/distance to each central region by empirical quantiles.
        # Keep observed academic score, hours and first-generation status.
        transported=np.zeros(len(t))
        for target_region in ['Montreal','Capitale-Nationale']:
            cf=d.copy().astype({'revenu_familial_estime':float,'distance_domicile_campus_km':float})
            for source_region in d.region_administrative.unique():
                mask=(d.region_administrative==source_region)
                hs=h.region_administrative==source_region
                ht=h.region_administrative==target_region
                for col in ['revenu_familial_estime','distance_domicile_campus_km']:
                    source=np.sort(h.loc[hs,col].to_numpy())
                    rank=np.searchsorted(source,d.loc[mask,col],side='right')/len(source)
                    cf.loc[mask,col]=np.quantile(h.loc[ht,col].to_numpy(),np.clip(rank,.001,.999))
            cf['region_administrative']=target_region
            tc=encode(cf).reindex(columns=x.columns,fill_value=0)
            # Encode with training categories; get_dummies(drop_first) on one region
            # otherwise drops the sole observed category.
            for col in x.columns:
                if col.startswith('region_administrative_'):
                    tc[col]=float(col=='region_administrative_'+target_region)
            transported+=model.predict_proba(tc)[:,1]/2
        save('model_D_boosted_regional_transport',transported,
             'Income/distance quantile transport to central regions; average Montreal and Capitale-Nationale predictions.',val)

# Gaussian latent-score model gives an independent estimate of the linear rule.
scaler=StandardScaler().fit(x)
xs=scaler.transform(x)
pm=Probit(y,np.column_stack([np.ones(len(x)),xs])).fit(disp=False)
coef=pd.Series(pm.params[1:],index=x.columns)
coef.to_csv(HERE/'probit_coefficients.csv',header=['standardized_coefficient'])
ts=scaler.transform(t)
score=ts[:,0]*coef['cote']+ts[:,1]*coef['hours']
save('model_E_probit_academic_hours',score,
     'Gaussian latent-score committee fit; retain learned academic and hours coefficients; neutralize all other effects.')
ensemble=np.zeros(len(t))
for name,weight in [('model_A_boosted_academic_hours',.25),
                    ('model_B_spline_academic_hours',.4),
                    ('model_E_probit_academic_hours',.35)]:
    ensemble+=weight*rankdata(np.load(HERE/f'{name}_scores.npy'))/len(t)
save('model_F_ensemble',ensemble,'Rank average: spline 40%, probit 35%, boosted trees 25%; weights chosen without hidden labels.')
np.savez(HERE/'model_diagnostics.npz',probit_coefficients=pm.params,probit_standard_errors=pm.bse)
(HERE/'model_manifest.json').write_text(json.dumps(records,indent=2)+'\n')
