for fic in lighting1_x10_bright.xml  lighting1_x10_off.xml lighting1_x10_dim.xml     lighting1_x10_on.xml
  do
    newFic=$(echo $fic | sed "s/1_x10/3_koppla/")
    sed  "s/1_x10/3_koppla/g" $fic > $newFic
    sed  "s/\"x10\"/\"koppla\"/g" $fic > $newFic
  done
