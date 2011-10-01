What should be done when publishing a new version?
==================================================

1) Change the version number of the application in the __init__.py module at the root directory of Domogik
2) If database modifications were made:
   * Change the value of 'CURRENT_DB_VERSION_NB' in db_installer.py
   * Add a function that will execute process in db_upgrade.py
