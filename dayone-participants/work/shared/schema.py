"""Shared, privacy-conscious clinical extraction schema."""
from __future__ import annotations

import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class Status(str, Enum):
    CONNU = "CONNU"
    INCONNU = "INCONNU"
    NON_FOURNI = "NON_FOURNI"
    ILLISIBLE = "ILLISIBLE"
    NON_APPLICABLE = "NON_APPLICABLE"
    A_REVISER = "À_RÉVISER"


IDENTIFIER_KEY = re.compile(r"(?:^|[._\[\]-])(?:nom|name|cin|telephone|phone|adresse|address|profession|husband_name)(?:$|[._\[\]-])", re.I)


class ClinicalField(BaseModel):
    key: str
    value: Any = None
    normalized: str | float | int | bool | None = None
    status: Status
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    page_type: int = Field(ge=1, le=8)
    bbox: tuple[float, float, float, float] | None = None
    raw_text: str | None = None

    @field_validator("key")
    @classmethod
    def reject_identifier_keys(cls, value: str) -> str:
        if IDENTIFIER_KEY.search(value):
            raise ValueError("identifier fields are excluded from the clinical schema")
        return value


class Page(BaseModel):
    page_type: int = Field(ge=1, le=8)
    patient_ref: str | None = None
    fields: list[ClinicalField]

    @field_validator("patient_ref")
    @classmethod
    def reject_direct_identifiers(cls, value: str | None) -> str | None:
        if value and not re.fullmatch(r"[A-Fa-f0-9]{8,32}", value):
            raise ValueError("patient_ref must be an opaque 8-32 character hexadecimal random code")
        return value

    @model_validator(mode="after")
    def validate_fields(self):
        keys = [field.key for field in self.fields]
        if len(keys) != len(set(keys)):
            raise ValueError("field keys must be unique within a page")
        if any(field.page_type != self.page_type for field in self.fields):
            raise ValueError("each field page_type must match its page")
        return self


FIELD_GROUPS = {
    1: "profile", 2: "history", 3: "current_pregnancy", 4: "delivery",
    5: "postpartum_mother", 6: "postpartum_newborn", 7: "late_postpartum_mother",
    8: "late_postpartum_newborn",
}

VISIT_OBSERVATIONS = (
    "appointment", "came_on", "follow_up", "probable_gestational_age", "weight", "blood_pressure",
    "skeleton", "conjunctivae", "breasts", "oedema", "active_movements", "fundal_height",
    "fetal_heart_rate", "speculum", "cervix", "presentation", "pelvis", "glycosuria",
    "albuminuria", "rubella", "toxoplasmosis", "syphilis", "hbs_ag", "hiv", "haemoglobin",
    "platelets", "glycaemia", "rai", "iron", "examiner",
)
PREVIOUS_DELIVERY_OBSERVATIONS = (
    "date", "mode", "caesarean_indication", "complication", "newborn_weight", "newborn_complication",
)

PREDEFINED_FIELDS = {
    1: ("profile.age", "profile.education", "profile.consanguinity", "profile.desired_pregnancy",
        "profile.region", "profile.province", "profile.facility", "profile.facility_type", "profile.coverage_mode", "profile.risk"),
    2: ("history.family_woman", "history.family_husband", "history.hypertension", "history.diabetes",
        "history.hereditary_disease", "history.malformations", "history.allergies", "history.abortion_count",
        "history.preterm_count", "history.fetal_death_count", "history.obstetric_events", "history.previous_deliveries",
        "history.gravidity", "history.parity", "history.living_children", "history.vat_doses",
        "history.rubella_vaccination", "history.hepatitis_b_vaccination", "history.smear"),
    3: ("pregnancy.ddr", "pregnancy.height", "pregnancy.blood_group", "pregnancy.rh", "pregnancy.edd",
        "pregnancy.term_exceeded_date", "pregnancy.visits"),
    4: ("delivery.place", "delivery.date", "delivery.mode", "delivery.emergency", "delivery.complications",
        "delivery.newborn_status", "delivery.sex", "delivery.weight", "delivery.head_circumference",
        "delivery.anomaly", "delivery.gestational_age"),
    5: ("postpartum_mother.date", "postpartum_mother.blood_pressure", "postpartum_mother.pulse",
        "postpartum_mother.weight", "postpartum_mother.temperature", "postpartum_mother.conjunctivae",
        "postpartum_mother.uterine_globe", "postpartum_mother.lochia", "postpartum_mother.perineum",
        "postpartum_mother.sphincters", "postpartum_mother.breasts", "postpartum_mother.calves",
        "postpartum_mother.complications", "postpartum_mother.medication", "postpartum_mother.treatment",
        "postpartum_mother.next_appointment", "postpartum_mother.family_planning"),
    6: ("newborn.date", "newborn.sex", "newborn.weight", "newborn.length", "newborn.head_circumference",
        "newborn.apgar", "newborn.resuscitation", "newborn.feeding", "newborn.exam", "newborn.complications",
        "newborn.treatment", "newborn.vaccination"),
    7: ("late_mother.date", "late_mother.blood_pressure", "late_mother.pulse", "late_mother.temperature",
        "late_mother.weight", "late_mother.exam", "late_mother.complications", "late_mother.treatment",
        "late_mother.family_planning"),
    8: ("late_newborn.date", "late_newborn.weight", "late_newborn.length", "late_newborn.head_circumference",
        "late_newborn.feeding", "late_newborn.exam", "late_newborn.complications", "late_newborn.treatment",
        "late_newborn.vaccination"),
}

PREDEFINED_FIELDS_ARE_PROVISIONAL = True
