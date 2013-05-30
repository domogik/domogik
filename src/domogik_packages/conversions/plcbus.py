class plcbusConversions():
    @staticmethod
    def from_DT_Switch_to_command(value):
        if (value == "1"):
            return 'ON'
        else:
            return 'OFF'

    @staticmethod
    def from_command_to_DT_Switch(value):
        if (value.upper() == 'ON'):
            return "1"
        else:
            return "0"
