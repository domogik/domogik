for fic in lighting1_x10_bright.xml  lighting1_x10_off.xml lighting1_x10_dim.xml     lighting1_x10_on.xml
  do
    newFic=$(echo $fic | sed "s/lighting1_x10/curtain1_harrison/")
    sed  "s/lighting1_x10/curtain1_harrison/g" $fic > $newFic
    sed  -i "s/\"x10\"/\"harrison\"/g" $newFic
  done
