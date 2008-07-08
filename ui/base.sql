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
-- Structure de la table `RItemsRooms`
-- 

CREATE TABLE `R_ITEMS_ROOMS` (
  `id` int(11) NOT NULL auto_increment,
  `item` int(11) NOT NULL,
  `room` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `FK_ELEMENT` (`item`),
  KEY `FK_ROOM` (`room`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=10 ;

-- 
-- Contenu de la table `RItemsRooms`
-- 

INSERT INTO `R_ITEMS_ROOMS` (`id`, `item`, `room`) VALUES 
(1, 1, 1),
(2, 2, 1),
(3, 3, 2),
(4, 3, 1),
(8, 4, 1),
(9, 5, 1);

-- --------------------------------------------------------

-- 
-- Structure de la table `RThermometerName`
-- 

CREATE TABLE `R_THERMOMETER_NAME` (
  `id` int(11) NOT NULL auto_increment,
  `id_thermo` varchar(16) NOT NULL,
  `label` varchar(50) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `id_thermo` (`id_thermo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

-- 
-- Contenu de la table `RThermometerNom`
-- 


-- --------------------------------------------------------

-- 
-- Structure de la table `RThermometerRooms`
-- 

CREATE TABLE `R_THERMOMETER_ROOMS` (
  `id` int(11) NOT NULL auto_increment,
  `thermometer` varchar(16) NOT NULL,
  `id_room` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `FK_THERMOMETER` (`thermometer`),
  KEY `FK_ROOM` (`id_room`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=2 ;

-- 
-- Contenu de la table `RThermometerRooms`
-- 

INSERT INTO `R_THERMOMETER_ROOMS` (`id`, `thermometer`, `id_room`) VALUES 
(1, '/28.12BB4B010000', 1);

-- --------------------------------------------------------

-- 
-- Structure de la table `Tstatements`
-- 

CREATE TABLE `T_STATEMENTS` (
  `id` int(11) NOT NULL auto_increment,
  `date` timestamp NOT NULL default CURRENT_TIMESTAMP,
  `thermometer` varchar(16) NOT NULL,
  `temperature` float NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `thermometer` (`thermometer`(1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=2842 ;

-- 
-- Contenu de la table `Tstatements`
-- 

INSERT INTO `T_STATEMENTS` (`id`, `date`, `thermometer`, `temperature`) VALUES 
(6, '2008-06-14 05:29:26', '/28.12BB4B010000', 23.2323),
(7, '2008-06-14 05:34:26', '/28.12BB4B010000', 23.2323),
(8, '2008-06-14 05:39:26', '/28.12BB4B010000', 23.875),
(9, '2008-06-14 05:44:27', '/28.12BB4B010000', 23.9375),
(10, '2008-06-14 05:49:27', '/28.12BB4B010000', 23.875);

-- --------------------------------------------------------

-- 
-- Structure de la table `capacities`
-- 

CREATE TABLE `CAPACITIES` (
  `id` int(11) NOT NULL auto_increment,
  `id_piece` int(11) NOT NULL,
  `capacity` enum('temperature','light','music') NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `FK_PIECE` (`id_piece`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=5 ;

-- 
-- Contenu de la table `capacities`
-- 

INSERT INTO `CAPACITIES` (`id`, `id_piece`, `capacity`) VALUES 
(2, 1, 'temperature'),
(3, 2, 'light'),
(4, 1, 'music');

-- --------------------------------------------------------

-- 
-- Structure de la table `items`
-- 

CREATE TABLE `ITEMS` (
  `id` int(11) NOT NULL auto_increment,
  `name` varchar(30) NOT NULL,
  `description` varchar(30) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=6 ;

-- 
-- Contenu de la table `items`
-- 

INSERT INTO `ITEMS` (`id`, `name`, `description`) VALUES 
(1, 'A1', 'lampe'),
(2, 'A2', 'chambre'),
(3, 'A3', 'guirlande'),
(4, 'A4', 'cafetière'),
(5, 'A5', 'music');

-- --------------------------------------------------------

-- 
-- Structure de la table `states`
-- 

CREATE TABLE `STATES` (
  `id` int(11) NOT NULL auto_increment,
  `item` int(11) NOT NULL,
  `state` tinyint(1) NOT NULL,
  `date` timestamp NOT NULL default CURRENT_TIMESTAMP,
  PRIMARY KEY  (`id`),
  KEY `item` (`item`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=6 ;

-- 
-- Contenu de la table `states`
-- 

INSERT INTO `STATES` (`id`, `item`, `state`, `date`) VALUES 
(1, 1, 1, '2008-05-20 21:12:22'),
(2, 2, 1, '2008-05-20 21:12:30'),
(3, 3, 0, '2008-05-20 23:05:44'),
(4, 4, 1, '2008-05-21 13:42:23'),
(5, 5, 0, '2008-05-21 13:42:23');

-- --------------------------------------------------------

-- 
-- Structure de la table `music`
-- 

CREATE TABLE `MUSIC` (
  `id` int(11) NOT NULL auto_increment,
  `id_piece` int(11) NOT NULL,
  `titre` varchar(150) NOT NULL,
  `temps` time NOT NULL,
  `temps_actuel` time NOT NULL,
  `state` enum('play','pause','stop') NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8 AUTO_INCREMENT=2 ;

-- 
-- Contenu de la table `music`
-- 

INSERT INTO `MUSIC` (`id`, `id_piece`, `titre`, `temps`, `temps_actuel`, `state`) VALUES 
(1, 1, 'Ma zoulie chanson', '00:03:17', '00:01:05', 'stop');

-- --------------------------------------------------------

-- 
-- Structure de la table `rooms`
-- 

CREATE TABLE `ROOMS` (
  `id` int(11) NOT NULL auto_increment,
  `name` varchar(30) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=3 ;

-- 
-- Contenu de la table `rooms`
-- 

INSERT INTO `ROOMS` (`id`, `name`) VALUES 
(1, 'chambre'),
(2, 'room de bain');

-- --------------------------------------------------------

-- 
-- Structure de la table `VStatesItems`
-- 

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `V_STATES_ITEMS` AS select `EL`.`name` AS `name`,`ET`.`state` AS `state`,`ET`.`date` AS `date`,`EL`.`description` AS `description` from (`STATES` `ET` join `ITEMS` `EL`) where (`ET`.`item` = `EL`.`id`);

-- --------------------------------------------------------

-- 
-- Structure de la table `VStatementsRooms`
-- 

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`%` SQL SECURITY DEFINER VIEW `V_STATEMENTS_ROOMS` AS select `TR`.`thermometer` AS `thermometer`,`TR`.`temperature` AS `temperature`,`TR`.`date` AS `date`,`S`.`name` AS `name` from ((`T_STATEMENTS` `TR` join `R_THERMOMETER_ROOMS` `TS`) join `ROOMS` `S`) where ((`TR`.`thermometer` = `TS`.`thermometer`) and (`TS`.`id_room` = `S`.`id`));

-- --------------------------------------------------------

-- 
-- Structure de la table `VItemsRooms`
-- 

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `V_ITEMS_ROOMS` AS select `ITEMS`.`name` AS `nameI`,`ROOMS`.`name` AS `nameR` from ((`ITEMS` join `ROOMS`) join `R_ITEMS_ROOMS`) where ((`ITEMS`.`id` = `R_ITEMS_ROOMS`.`item`) and (`R_ITEMS_ROOMS`.`room` = `ROOMS`.`id`));

-- 
-- Contraintes pour les tables exportées
-- 

-- 
-- Contraintes pour la table `RItemsRooms`
-- 
ALTER TABLE `R_ITEMS_ROOMS`
  ADD CONSTRAINT `R_ITEMS_ROOMS_ibfk_7` FOREIGN KEY (`item`) REFERENCES `ITEMS` (`id`) ON DELETE NO ACTION,
  ADD CONSTRAINT `R_ITEMS_ROOMS_ibfk_8` FOREIGN KEY (`room`) REFERENCES `ROOMS` (`id`) ON DELETE NO ACTION;

-- 
-- Contraintes pour la table `capacities`
-- 
ALTER TABLE `CAPACITIES`
  ADD CONSTRAINT `CAPACITIES_ibfk_1` FOREIGN KEY (`id_piece`) REFERENCES `ROOMS` (`id`);

-- 
-- Contraintes pour la table `states`
-- 
ALTER TABLE `STATES`
  ADD CONSTRAINT `STATES_ibfk_1` FOREIGN KEY (`item`) REFERENCES `ITEMS` (`id`);

