=== Informations sur la version actuelle de l'interface ===
L'interface est programmée en php5 avec le framework CodeIgniter.
Les répertoires :
* config/
* controllers/
* views/
* models/
doivent être mis dans le répertoire system/application de CodeIgniter

Le répertoire include/ doit être mis à la racine du répertoire web (avec la config actuelle)

De plus, la librairie 'database' doit être ajoutée dans les préchargements (fichier system/application/config/autoload.php de l'installation CI).

Fonctionnement :

L'interface permet de visualiser des pièces, affichées dans le menu gauche. Ces pièces sont définies dans la table 'salle'⋅
Chaque pièce possède un certain nombre de capacités (ou fonctionnalités). Les capacités possibles (à l'heure actuelle) sont 
'temperature', 'lumiere', 'musique'. La liste des capacités de chaque pièce est définie dans la table 'capacites'. 
Les capacités d'une pièce sont affichées à droite de l'interface.

Détail des capacités :

Lumière :

La capacité 'lumière' a pour but de récupérer l'état d'éléments électriques d'une pièce (lumière, prise).
La liste des éléments associés à une pièce est définie dans la table 'element'. 
Les relations element <=> salle sont définies dans la table RElementsSalles.
L'état d'un élément est défini dans la table "etats".
L'état d'un élément est donc récupéré régulièrement par l'interface (par défaut toutes les 3 secondes),
et un item rouge ou vert est alors affiché.

Température :

La table 'Treleves' Permet de stocker des enregistrements contenant l'identifiant d'un thermomètre, la date/heure de relevé et la valeur du relevé.
Chaque pièce peut posséder un certain nombre de thermomètres. Les appartenances sont définies dans la table RThermometreSalles.
La table RThermometreNom permet également de donner un nom/descriptif pour chaque thermomètre.
La page température de l'interace récupère la liste des relevés des dernières 24heures pour la pièce courante, et génère un graphique à 
l'aide de la librairie jsgraph.
Ce graphique est actualisé toutes les 5 minutes (par défaut).

Musique :

La page Musique permet de controler un éventuel lecteur audio. Elle utilise la table 'musique' pour déterminer des informations sur le morceau lu, 
à savoir :
- le titre
- le temps total
- le temps courant
- l'état de la lecture (play, pause, stop).

Les données sont rafraichies toutes les 2 secondes. Les boutons Play, Pause, Stop sont activés ou désactivés suivant l'état de la lecture.

Maxence (maxence@dunnewind.net)

