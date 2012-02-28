for PROTO in arc elro waveman chacon impuls
  do
    for fic in lighting1_x10_bright.xml  lighting1_x10_off.xml lighting1_x10_dim.xml     lighting1_x10_on.xml
      do
        newFic=$(echo $fic | sed "s/x10/$PROTO/")
        sed  "s/x10/$PROTO/g" $fic > $newFic
      done
  done
