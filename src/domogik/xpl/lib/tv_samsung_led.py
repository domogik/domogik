COMMANDS = {
"power_standby" : "00000001", # Power Standby    ### OK
"power_on" : "00000002", # Power On              ### OK
"get_power_status" : "00000000", # Get power status   ### ?????
"mute_toggle" : "02000000", # Mute toggle        ### OK
"volume_up" : "01000100", # Master Volume Up     ### OK
"volume_down" : "01000200", # Master Volume Down     ### OK
"channel_up" : "03000100", # Channel Up    ### OK
"channel_down" : "03000200", # Channel Down  ### ERR
"tv" : "0a000000", # TV       ### OK
"av1" : "0a000100", # AV 1       ### OK
"av2" : "0a000101", # AV 2       ### OK
"av3" : "0a000102", # AV 3       ### OK
"svideo1" : "0a000200", # S-Video 1     ### OK
"svideo2" : "0a000201", # S-Video 2     ### OK
"component1" : "0a000300", # Component 1    ### OK
"component3" : "0a000302", # Component 3    ### OK
"pc1" : "0a000400", # PC 1     ### OK
"pc2" : "0a000401", # PC 2     ### OK
"hdmi1" : "0a000500", # HDMI 1   ### OK
"hdmi2" : "0a000501", # HDMI 2   ### OK
"hdmi3" : "0a000502", # HDMI 3   ### OK
"hdmi4" : "0a000503", # HDMI 4   ### OK
"dvi1" : "0a000600", # DVI 1   ### OK
"dvi2" : "0a000601", # DVI 2   ### OK
"dvi3" : "0a000602", # DVI 3   ### OK
"dynamic" : "0b000000", # Dynamic
"standard" : "0c000000", # Standard
"wide" : "0b000002", # Wide
"black_adjust_off" : "0b090000", # Black Adjust Off
"black_adjust_medium" : "0b090002", # Black Adjust Medium
"black_adjust_low" : "0b090001", # Black Adjust Low
"black_adjust_high" : "0b090003", # Black Adjust High
"dynamic_contrast_off" : "0b090100", # Dynamic Contrast Off
"dynamic_contrast_low" : "0b090101", # Dynamic Contrast Low
"dynamic_contrast_medium" : "0b090102", # Dynamic Contrast Medium
"dynamic_contrast_high" : "0b090103", # Dynamic Contrast High
"color_space_auto" : "0b090300", # Color Space Auto
"color_space_wide" : "0b090301", # Color Space Wide

# Others
"aspect_16_9" : "0b0a0100", # 16/9 aspect
"aspect_zoom_1" : "0b0a0101", # Zoom 1 aspect
"aspect_zoom_2" : "0b0a0102", # Zoom 2 aspect
"aspect_wide_fit" : "0b0a0103", # Wide Fit aspect
"aspect_4_3" : "0b0a0104", # 4/3 aspect
"speaker_off" : "0c060000", # Speaker Off
"speaker_on" : "0c060001", # Speaker On

# Sound commands
"sound_standard" : "0c000000", # Standard
"sound_music" : "0c000001", # Music
"sound_movie" : "0c000002", # Movie
"sound_custom" : "0c000004", # Custom
"sound_eq_standard" : "0c010000", # EQ Standard
"sound_eq_music" : "0c010001", # EQ Music
"sound_eq_video" : "0c010002", # EQ Movie
"sound_eq_speech" : "0c010003", # EQ Speech
"sound_eq_custom" : "0c010004", # EQ Custom
"sound_srs_tru_surround_on" : "0c020000", # SRS Tru Surround On
"sound_srs_tru_surround_off" : "0c020001", # SRS Tru Surround Off
"sound_multi_track_mono" : "0c040000", # Multi-Track Mono
"sound_multi_track_stereo" : "0c040001", # Multi-Track Stereo
"sound_multi_track_sap" : "0c040002", # Multi-Track SAP

# Tests
"test" : "01000005", # Sound level 5/100
#"test" : "04010002", # Channel 2 on TNT
#"test" : "04000002", # Channel 2 on Classical TV
}
