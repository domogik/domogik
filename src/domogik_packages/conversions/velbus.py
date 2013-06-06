class velbusConversions():
    @staticmethod
    def from_DT_Switch_to_level(x):
        if x == '1':
            return int(255)
        else:
            return int(0)

    @staticmethod
    def from_DT_Scaling_to_level(x):
        # 0 - 100 translated to 0 - 255
        return round(int(x) / 100 * 255)

    @staticmethod
    def from_level_to_DT_Switch(x):
        if x == '255':
            return int(1)
        if x == '0':
            return int(0)

    @staticmethod
    def from_level_to_DT_Scaling(x):
        # 0 - 255 translated to 0 - 100
        return round(int(x) / 255 * 100)

    @staticmethod
    def from_input_to_DT_State(x):
        if x == 'LOW':
            return 0
        else:
            return 1
