import type { ErrorCode } from '../contracts';

const MESSAGES: Record<ErrorCode, string> = {
  NO_REFERENCE: "Je ne vois pas la feuille de référence en entier. Reculez un peu et cadrez toute la feuille.",
  REFERENCE_TILTED: "La feuille est trop inclinée. Tenez le téléphone bien à plat au-dessus.",
  BLURRY: "La photo est floue. Tenez le téléphone immobile et touchez l'écran pour faire la mise au point.",
  NO_LENS: "Je ne trouve pas le verre. Posez-le au centre de la fenêtre.",
  LENS_OUT_OF_WINDOW: "Le verre dépasse de la fenêtre. Recentrez-le.",
  GLARE: "Il y a un reflet sur le verre. Éteignez le flash ou changez légèrement d'angle.",
  INCONSISTENT_SHOTS: "Les photos ne donnent pas la même mesure. Reprenons une photo sans bouger le verre.",
  LENS_ROTATED: "Le verre semble posé de travers. Alignez-le sur la ligne guide.",
  CAMERA_DENIED: "L'accès à la caméra est refusé. Vous pouvez importer une photo à la place.",
  LOAD_FAILED: "Le chargement a échoué. Vérifiez la connexion puis rechargez la page.",
};

export function messageFor(code: ErrorCode): string {
  return MESSAGES[code] ?? MESSAGES.LOAD_FAILED;
}
