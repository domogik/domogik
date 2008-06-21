-- phpMyAdmin SQL Dump
-- version 2.9.1.1-Debian-2ubuntu1.2
-- http://www.phpmyadmin.net
-- 
-- Serveur: localhost
-- Généré le : Lundi 16 Juin 2008 à 19:52
-- Version du serveur: 5.0.38
-- Version de PHP: 5.2.1
-- 
-- Base de données: `domogik`
-- 

-- --------------------------------------------------------

-- 
-- Structure de la table `RElementsSalles`
-- 

CREATE TABLE `RElementsSalles` (
  `id` int(11) NOT NULL auto_increment,
  `element` int(11) NOT NULL,
  `salle` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `FK_ELEMENT` (`element`),
  KEY `FK_SALLE` (`salle`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=10 ;

-- 
-- Contenu de la table `RElementsSalles`
-- 

INSERT INTO `RElementsSalles` (`id`, `element`, `salle`) VALUES 
(1, 1, 1),
(2, 2, 1),
(3, 3, 2),
(4, 3, 1),
(8, 4, 1),
(9, 5, 1);

-- --------------------------------------------------------

-- 
-- Structure de la table `RThermometreNom`
-- 

CREATE TABLE `RThermometreNom` (
  `id` int(11) NOT NULL auto_increment,
  `id_thermo` varchar(16) NOT NULL,
  `label` varchar(50) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `id_thermo` (`id_thermo`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- 
-- Contenu de la table `RThermometreNom`
-- 


-- --------------------------------------------------------

-- 
-- Structure de la table `RThermometreSalles`
-- 

CREATE TABLE `RThermometreSalles` (
  `id` int(11) NOT NULL auto_increment,
  `thermometre` varchar(16) NOT NULL,
  `id_salle` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `FK_THERMOMETRE` (`thermometre`),
  KEY `FK_SALLE` (`id_salle`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=2 ;

-- 
-- Contenu de la table `RThermometreSalles`
-- 

INSERT INTO `RThermometreSalles` (`id`, `thermometre`, `id_salle`) VALUES 
(1, '/28.12BB4B010000', 1);

-- --------------------------------------------------------

-- 
-- Structure de la table `Treleves`
-- 

CREATE TABLE `Treleves` (
  `id` int(11) NOT NULL auto_increment,
  `date` timestamp NOT NULL default CURRENT_TIMESTAMP,
  `thermometre` varchar(16) NOT NULL,
  `temperature` float NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `thermometre` (`thermometre`(1))
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=2842 ;

-- 
-- Contenu de la table `Treleves`
-- 

INSERT INTO `Treleves` (`id`, `date`, `thermometre`, `temperature`) VALUES 
(6, '2008-06-14 05:29:26', '/28.12BB4B010000', 23.2323),
(7, '2008-06-14 05:34:26', '/28.12BB4B010000', 23.2323),
(8, '2008-06-14 05:39:26', '/28.12BB4B010000', 23.875),
(9, '2008-06-14 05:44:27', '/28.12BB4B010000', 23.9375),
(10, '2008-06-14 05:49:27', '/28.12BB4B010000', 23.875);

-- --------------------------------------------------------

-- 
-- Structure de la table `capacites`
-- 

CREATE TABLE `capacites` (
  `id` int(11) NOT NULL auto_increment,
  `id_piece` int(11) NOT NULL,
  `capacite` enum('temperature','lumiere','musique') NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `FK_PIECE` (`id_piece`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=5 ;

-- 
-- Contenu de la table `capacites`
-- 

INSERT INTO `capacites` (`id`, `id_piece`, `capacite`) VALUES 
(2, 1, 'temperature'),
(3, 2, 'lumiere'),
(4, 1, 'musique');

-- --------------------------------------------------------

-- 
-- Structure de la table `elements`
-- 

CREATE TABLE `elements` (
  `id` int(11) NOT NULL auto_increment,
  `nom` varchar(30) NOT NULL,
  `description` varchar(30) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=6 ;

-- 
-- Contenu de la table `elements`
-- 

INSERT INTO `elements` (`id`, `nom`, `description`) VALUES 
(1, 'A1', 'lampe'),
(2, 'A2', 'chambre'),
(3, 'A3', 'guirlande'),
(4, 'A4', 'cafetière'),
(5, 'A5', 'musique');

-- --------------------------------------------------------

-- 
-- Structure de la table `etats`
-- 

CREATE TABLE `etats` (
  `id` int(11) NOT NULL auto_increment,
  `element` int(11) NOT NULL,
  `etat` tinyint(1) NOT NULL,
  `date` timestamp NOT NULL default CURRENT_TIMESTAMP,
  PRIMARY KEY  (`id`),
  KEY `element` (`element`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=6 ;

-- 
-- Contenu de la table `etats`
-- 

INSERT INTO `etats` (`id`, `element`, `etat`, `date`) VALUES 
(1, 1, 1, '2008-05-20 21:12:22'),
(2, 2, 1, '2008-05-20 21:12:30'),
(3, 3, 0, '2008-05-20 23:05:44'),
(4, 4, 1, '2008-05-21 13:42:23'),
(5, 5, 0, '2008-05-21 13:42:23');

-- --------------------------------------------------------

-- 
-- Structure de la table `musique`
-- 

CREATE TABLE `musique` (
  `id` int(11) NOT NULL auto_increment,
  `id_piece` int(11) NOT NULL,
  `titre` varchar(150) NOT NULL,
  `temps` time NOT NULL,
  `temps_actuel` time NOT NULL,
  `etat` enum('play','pause','stop') NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM  DEFAULT CHARSET=latin1 AUTO_INCREMENT=2 ;

-- 
-- Contenu de la table `musique`
-- 

INSERT INTO `musique` (`id`, `id_piece`, `titre`, `temps`, `temps_actuel`, `etat`) VALUES 
(1, 1, 'Ma zoulie chanson', '00:03:17', '00:01:05', 'stop');

-- --------------------------------------------------------

-- 
-- Structure de la table `salles`
-- 

CREATE TABLE `salles` (
  `id` int(11) NOT NULL auto_increment,
  `nom` varchar(30) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=3 ;

-- 
-- Contenu de la table `salles`
-- 

INSERT INTO `salles` (`id`, `nom`) VALUES 
(1, 'chambre'),
(2, 'salle de bain');

-- --------------------------------------------------------

-- 
-- Structure de la table `VEtatsElements`
-- 

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `domogik`.`VEtatsElements` AS select `EL`.`nom` AS `nom`,`ET`.`etat` AS `etat`,`ET`.`date` AS `date`,`EL`.`description` AS `description` from (`domogik`.`etats` `ET` join `domogik`.`elements` `EL`) where (`ET`.`element` = `EL`.`id`);

-- --------------------------------------------------------

-- 
-- Structure de la table `VRelevesSalles`
-- 

CREATE ALGORITHM=UNDEFINED DEFINER=`domogik`@`%` SQL SECURITY DEFINER VIEW `domogik`.`VRelevesSalles` AS select `TR`.`thermometre` AS `thermometre`,`TR`.`temperature` AS `temperature`,`TR`.`date` AS `date`,`S`.`nom` AS `nom` from ((`domogik`.`Treleves` `TR` join `domogik`.`RThermometreSalles` `TS`) join `domogik`.`salles` `S`) where ((`TR`.`thermometre` = `TS`.`thermometre`) and (`TS`.`id_salle` = `S`.`id`));

-- --------------------------------------------------------

-- 
-- Structure de la table `vue`
-- 

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `domogik`.`vue` AS select `domogik`.`elements`.`nom` AS `nomE`,`domogik`.`salles`.`nom` AS `nomS` from ((`domogik`.`elements` join `domogik`.`salles`) join `domogik`.`RElementsSalles`) where ((`domogik`.`elements`.`id` = `domogik`.`RElementsSalles`.`element`) and (`domogik`.`RElementsSalles`.`salle` = `domogik`.`salles`.`id`));

-- 
-- Contraintes pour les tables exportées
-- 

-- 
-- Contraintes pour la table `RElementsSalles`
-- 
ALTER TABLE `RElementsSalles`
  ADD CONSTRAINT `RElementsSalles_ibfk_7` FOREIGN KEY (`element`) REFERENCES `elements` (`id`) ON DELETE NO ACTION,
  ADD CONSTRAINT `RElementsSalles_ibfk_8` FOREIGN KEY (`salle`) REFERENCES `salles` (`id`) ON DELETE NO ACTION;

-- 
-- Contraintes pour la table `capacites`
-- 
ALTER TABLE `capacites`
  ADD CONSTRAINT `capacites_ibfk_1` FOREIGN KEY (`id_piece`) REFERENCES `salles` (`id`);

-- 
-- Contraintes pour la table `etats`
-- 
ALTER TABLE `etats`
  ADD CONSTRAINT `etats_ibfk_1` FOREIGN KEY (`element`) REFERENCES `elements` (`id`);

