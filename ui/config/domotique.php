<?php  if (!defined('BASEPATH')) exit('No direct script access allowed');
$config = array();

/*******************************/
/*  Temps de rafraîchissement  */
/*******************************/

//Page des lumières & prises
$config['LIGHT_REFRESH'] = 3; //3 secondes

//Page des températures
$config['TEMP_REFRESH'] = 300; //5 minutes

//Page pour la musique
$config['AUDIO_REFRESH'] = 2; //2 secondes

/******************************/
/*       Capacités            */
/******************************/
/*
 * Les capacités permettent de décrire quelle fonctionnalité
 * est présente dans chaque pièce.
 * Elles sont décrites dans la table 'capacites'
 * Ce tableau défini quelle fonction doit être appelée pour chaque capacités
 * La fonction doit être présente dans le controlleur Piece
 */
$config['CAPACITIES'] = array(
"temperature" => "temperature",
"musique" => "audio",
"lumiere" => "lumiere"
);

?>
