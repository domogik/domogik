for PROTO in homeasy_eu
  do
    for fic in lighting2_ac_on.xml lighting2_ac_off.xml lighting2_ac_preset.xml 
      do
        newFic=$(echo $fic | sed "s/ac/$PROTO/")
        sed  "s/lighting2_ac/lighting2_$PROTO/g" $fic > $newFic
      done
  done
