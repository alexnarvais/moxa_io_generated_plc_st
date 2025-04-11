import csv
from abc import ABC
from moxa_exceptions import (
    MoxaIoError,
    MultiSlotError,
    DuplRackError,
    ChanNumRackError,
    ChanTypeRackError
)


class MoxaFileProc:
    def __init__(self, rd_file_path, wr_file_path):
        self._rd_file_path = rd_file_path
        self._wr_file_path = wr_file_path

    def read_moxa_io_csv(self):
        io = {}
        supported = {'e1210': {}, 'e1212': {}, 'e1240': {}, 'e1241': {}, 'e1260': {}}

        for _ in range(16):
            supported['e1210'][_] = ['di']
        for _ in range(16):
            supported['e1212'][_] = ['di'] if _ < 8 else ['di', 'do']
        for _ in range(8):
            supported['e1240'][_] = ['ai']
        for _ in range(4):
            supported['e1241'][_] = ['ao']
        for _ in range(6):
            supported['e1260'][_] = ['rtd']

        if self._rd_file_path:
            # Open the csv file
            with open(self._rd_file_path) as csv_file:
                csv_rd_obj = csv.reader(csv_file, delimiter=',')
                next(csv_rd_obj, None)  # Ignore the header row
                for row in csv_rd_obj:
                    rack_num, slot_num, slot_type, channel_num, channel_type, tag_name, raw_min, raw_max, eu_min, eu_max, use_counts = row
                    rack = io.get(rack_num)
                    if not rack:
                        io[rack_num] = {}
                        rack = io.get(rack_num)
                    slot = rack.get(slot_num)
                    if not slot:
                        if slot_type in supported.keys():
                            rack[slot_num] = {'slot_type': slot_type, 'channels': {}}
                            slot = rack.get(slot_num)
                        else:
                            raise MoxaIoError(f'Error in configuration: unsupported slot type for rack {rack_num} slot {slot_num}: {slot_type}')
                            continue
                    else:  # check to see if there are incorrect slot_types
                        if slot_type != slot.get('slot_type'):
                            raise MultiSlotError(f'Error in configuration: multiple slot types found for rack {rack_num} slot {slot_num}. {slot_type} and {slot.get("slot_type")}')
                            continue
                    channel = slot['channels'].get(channel_num)
                    if channel:  # we have already added this channel something is wrong
                        raise ChanNumRackError(f'Error in configuration: duplicate channel for rack[{rack_num}]/slot[{slot_num}]/channel[{channel_num}]')
                        continue
                    if int(channel_num) not in supported[slot_type].keys():
                        raise DuplRackError(f'Error in configuration: unsupported channel number rack[{rack_num}]/slot[{slot_num}]/channel[{channel_num}]')
                        continue
                    if channel_type not in supported[slot_type][int(channel_num)]:
                        raise ChanTypeRackError(f'Error in configuration: unsupported channel type for rack[{rack_num}]/slot[{slot_num}]/channel[{channel_num}]')
                        continue
                    slot['channels'][channel_num] = {'channel_type': channel_type, 'tag_name': tag_name,
                                                     'scaling': {"raw_min": raw_min, "raw_max": raw_max,
                                                                 "eu_min": eu_min, "eu_max": eu_max,
                                                                 "use_counts": use_counts}}
        return io

    def wr_moxa_io_txt(self, io):
        output_text_list = []
        for rack_name in io.keys():
            rack = io[rack_name]
            for slot_name in rack.keys():
                slot = rack[slot_name]
                slot_type = slot['slot_type']
                match slot_type:
                    case "e1210":
                        output_text_list.append('/////////////////////////////////////////////////////////////////////')
                        e1210 = MoxaE1210(int(rack_name), int(slot_name), slot_type, slot)
                        output_text_list.extend(e1210.rack__slot_e1210_list)
                    case "e1212":
                        output_text_list.append('/////////////////////////////////////////////////////////////////////')
                        e1212 = MoxaE1212(int(rack_name), int(slot_name), slot_type, slot)
                        output_text_list.extend(e1212.rack__slot_e1212_list)
                    case "e1240":
                        output_text_list.append('/////////////////////////////////////////////////////////////////////')
                        e1240 = MoxaE1240(int(rack_name), int(slot_name), slot_type, slot)
                        output_text_list.extend(e1240.rack__slot_e1240_list)
                    case "e1241":
                        output_text_list.append('/////////////////////////////////////////////////////////////////////')
                        e1241 = MoxaE1241(int(rack_name), int(slot_name), slot_type, slot)
                        output_text_list.extend(e1241.rack__slot_e1241_list)
                    case "e1260":
                        output_text_list.append('/////////////////////////////////////////////////////////////////////')
                        e1260 = MoxaE1260(int(rack_name), int(slot_name), slot_type, slot)
                        output_text_list.extend(e1260.rack__slot_e1260_list)
                    case _:
                        print("No match?")
        with open(self._wr_file_path, 'wt', encoding='utf8') as out_file:
            out_file.write('\n'.join(output_text_list))


class MoxaE1200(ABC):
    def __init__(self, rack_num, slot_num, slot_type):
        # Private attributes that can be accessed using the properties defined below.
        self.__rack_num = rack_num
        self.__slot_num = slot_num
        self.__slot_type = slot_type
        self.__rs= f'r{self.rack_num:02}s{self.slot_num:02}'
        self.__comm_config = self.generate_base_comm_config()

    # These properties will be used in the child classes
    # to access the private attributes defined here in the parent class.
    @property
    def rack_num(self):
        return self.__rack_num

    @rack_num.setter
    def rack_num(self, rn):
        self.__rack_num = rn

    @property
    def slot_num(self):
        return self.__slot_num

    @slot_num.setter
    def slot_num(self, sn):
        self.__slot_num = sn

    @property
    def slot_type(self):
        return self.__slot_type

    @slot_type.setter
    def slot_type(self, st):
        self.__slot_type = st

    @property
    def rack_slot(self):
        return self.__rs

    @rack_slot.setter
    def rack_slot(self, rs):
        self.__rs= rs

    @property
    def comm_config(self):
        return self.__comm_config

    @comm_config.setter
    def comm_config(self, comm_config):
        self.__comm_config = comm_config

    def generate_base_comm_config(self):
        return [
            f"// Rack {self.rack_num} Slot {self.slot_num}",
            "// This code was generated by python. Please make corrections in the csv file, rerun the code and re-paste",
            "// Get the module status",
            f"GSV(Module, {self.rack_slot}_moxa_{self.slot_type}, EntryStatus, r{self.rack_num:02}s{self.slot_num:02}_module_status);",
            '// Get 4 bits from 12 - 15 and put into separate DINT',
            f'{self.rack_slot}_btdt_1.Source := {self.rack_slot}_module_status;',
            f'{self.rack_slot}_btdt_1.SourceBit := 12;',
            f'{self.rack_slot}_btdt_1.Length := 4;',
            f'{self.rack_slot}_btdt_1.DestBit := 0;',
            f'{self.rack_slot}_btdt_1.Target := zero;',
            f'BTDT({self.rack_slot}_btdt_1);',
            f'{self.rack_slot}_module_status_easy := {self.rack_slot}_btdt_1.Dest;',
                     '',
                     '// If this is the first time the DINT is equal to something other than 4, see why',
                     f'{self.rack_slot}_osri_1.InputBit := ({self.rack_slot}_module_status_easy <> 4);',
                     f'OSRI({self.rack_slot}_osri_1);',
                     f'if {self.rack_slot}_osri_1.OutputBit then',
                     f'   GSV(Module, {self.rack_slot}_moxa_{self.slot_type}, FaultCode, {self.rack_slot}_fault_code);',
                     f'   GSV(Module, {self.rack_slot}_moxa_{self.slot_type}, FaultInfo, {self.rack_slot}_fault_info);',
                     'end_if;',
                     '',
                     '// The connection is good, if the module states is equal to 4',
                     f'{self.rack_slot}_connection_error := ({self.rack_slot}_module_status_easy <> 4);',
                     '',
                     '// Set the av program input for the fault code',
                     f'AOI_AV(aoi_{self.rack_slot}_comm_fault_code, av_{self.rack_slot}_comm_fault_code);',
                     f'av_{self.rack_slot}_comm_fault_code.Program_Input := {self.rack_slot}_fault_code;',
                     '',
                     '// Set the av program input for the fault info',
                     f'AOI_AV(aoi_{self.rack_slot}_Comm_Fault_Info, Av_{self.rack_slot}_Comm_Fault_Info);',
                     f'AV_{self.rack_slot}_Comm_Fault_Info.Program_Input := {self.rack_slot}_fault_info;',
                     '',
                     '// Set the comm status dv',
                     f'AOI_DV(aoi_{self.rack_slot}_comm_status, dv_{self.rack_slot}_comm_status);',
                     f'dv_{self.rack_slot}_comm_status.Program_Input := NOT {self.rack_slot}_connection_error AND NOT {self.rack_slot}_moxa_{self.slot_type}:I.ConnectionFaulted;',
                     ''
        ]

    def clear_unused_bits_analog(self):
        rsl = ['// Clear the unused bits in the unreliable DINT',
               f'{self.rack_slot}_btdt_2.Source := zero;',
               f'{self.rack_slot}_btdt_2.SourceBit := 0;',
               f'{self.rack_slot}_btdt_2.Length := 24;',
               f'{self.rack_slot}_btdt_2.DestBit := 8;',
               f'{self.rack_slot}_btdt_2.Target := {self.rack_slot}_unreliable;',
               f'BTDT({self.rack_slot}_btdt_2);',
               f'{self.rack_slot}_unreliable := {self.rack_slot}_btdt_2.Dest;',
               '',
               '// Clear the unused bits in the manual DINT', f'{self.rack_slot}_btdt_3.Source := zero;',
               f'{self.rack_slot}_btdt_3.SourceBit := 0;', f'{self.rack_slot}_btdt_3.Length := 24;',
               f'{self.rack_slot}_btdt_3.DestBit := 8;',
               f'{self.rack_slot}_btdt_3.Target := {self.rack_slot}_manual;',
               f'BTDT({self.rack_slot}_btdt_3);',
               f'{self.rack_slot}_manual := {self.rack_slot}_btdt_3.Dest;',
               '']

        return rsl


class MoxaE1212(MoxaE1200):
    def __init__(self, rack_num, slot_num, slot_type, slot):
        super(MoxaE1212, self).__init__(rack_num, slot_num, slot_type)
        self.__slot = slot
        self._rsl_e1212 = [f'// Moxa Digital Inputs and Outputs E1212']
        self._rsl_e1212.extend(self.comm_config)
        # channels
        channels = self.__slot['channels']
        channel_list = [int(x) for x in list(channels.keys())]
        channel_list.sort()
        channel_list = [str(x) for x in channel_list]
        for channel_number in channel_list:
            channel = channels[channel_number]
            cn = int(channel_number)
            tag_name = channel['tag_name']
            if not tag_name:
                self._rsl_e1212.append(f'// Channel {cn} - Spare')
            else:
                if channel['channel_type'] == 'di':
                    self._rsl_e1212.append(f'// Channel {cn} - input - {tag_name}')
                    self._rsl_e1212.append('// Process the AOI')
                    self._rsl_e1212.append(f'AOI_DI(aoi_{self.rack__slot}c{cn:02}, {tag_name});')
                    self._rsl_e1212.append('// Set the program input of the UDT')
                    word = 0 if cn < 8 else 1
                    bit = cn if cn < 8 else cn - 8
                    self._rsl_e1212.append(
                        f'{tag_name}.Program_Input := {self.rack__slot}_moxa_{self.slot_type}:I.Data[{word}].{bit};')
                    self._rsl_e1212.append('// Set the channel in manual bit in the manual DINT')
                    self._rsl_e1212.append(f'{self.rack__slot}_manual.{cn} := {tag_name}.Manual;')
                else:
                    self._rsl_e1212.append(f'// Channel {cn} - output - {tag_name}')
                    self._rsl_e1212.append('// Process the AOI')
                    self._rsl_e1212.append(
                        f'AOI_DO(aoi_{self.rack__slot}c{cn:02}, {self.rack__slot}c{cn:02}, {tag_name});')
                    self._rsl_e1212.append('// set the output value from the intermediate BOOL')
                    bit = cn - 8  # only channels 8-15 can be outputs
                    self._rsl_e1212.append(
                        f'{self.rack__slot}_moxa_{self.slot_type}:O.Data[0].{bit} := {self.rack__slot}c{cn:02};')
            self._rsl_e1212.append('')

    @property
    def rack__slot_e1212_list(self):
        return self._rsl_e1212

    @rack__slot_e1212_list.setter
    def rack__slot_e1212_list(self, rsl_e1212):
        self._rsl_e1212 = rsl_e1212


class MoxaE1210(MoxaE1200):
    def __init__(self, rack_num, slot_num, slot_type, slot):
        super(MoxaE1210, self).__init__(rack_num, slot_num, slot_type)
        self.__slot = slot
        self.__e1210_config = [f'// Moxa Digital Input E1210', *self.comm_config]
        # Channels
        channels = self.__slot['channels']
        channel_list = [int(x) for x in list(channels.keys())]
        channel_list.sort()
        channel_list = [str(x) for x in channel_list]
        for channel_number in channel_list:
            channel = channels[channel_number]
            cn = int(channel_number)
            tag_name = channel['tag_name']
            if not tag_name:
                self._rsl_e1210.append(f'// Channel {cn} - Spare')
            else:
                self._rsl_e1210.append(f'// Channel {cn} - input - {tag_name}')
                self._rsl_e1210.append('// Process the AOI')
                self._rsl_e1210.append(f'AOI_DI(aoi_{self.rack__slot}c{cn:02}, {tag_name});')
                self._rsl_e1210.append('// Set the program input of the UDT')
                word = 0 if cn < 16 else 1
                bit = cn if cn < 16 else cn - 16
                self._rsl_e1210.append(
                    f'{tag_name}.Program_Input := {self.rack__slot}_moxa_{self.slot_type}:I.Data[{word}].{bit};')
                self._rsl_e1210.append('// Set the channel in manual bit in the manual DINT')
                self._rsl_e1210.append(f'{self.rack__slot}_manual.{cn} := {tag_name}.Manual;')
            self._rsl_e1210.append('')

    @property
    def e1210_config(self):
        return self.__e1210_config

    @e1210_config.setter
    def e1210_config(self, e1210):
        self.__e1210_config = e1210


class MoxaE1240(MoxaE1200):
    def __init__(self, rack_num, slot_num, slot_type, slot):
        super(MoxaE1240, self).__init__(rack_num, slot_num, slot_type)
        self.__slot = slot
        self._rsl_e1240 = [f'// Moxa Analog Inputs E1240']
        # A call to the parent property member which holds the communication settings.
        self._rsl_e1240.extend(self.comm_config)
        # A call to the clear_unused_bits_analog parent method.
        self._rsl_e1240.extend(self.clear_unused_bits_analog())
        self._rsl_e1240.append('// The raw low and high for an analog input/output is based on a 0-20ma signal.')
        self._rsl_e1240.append("/*\n"
                               "   The low and high for an rtd will be based on the raw side which comes in one decimal to the\n"
                               "   right to large. If for example a value above 150 or below -5 deg F should cause a fault, then on the raw side\n "
                               "  you would set the [tag].Fault.Program_Input_Hi = 1500 and [tag].Fault.Program_Input_Lo = -50\n"
                               "*/")
        self._rsl_e1240.append('// ---------------------------------')
        self._rsl_e1240.append('// | Signal        | High  | Low   |')
        self._rsl_e1240.append('// | ------------- |-------|-------|')
        self._rsl_e1240.append('// | Analog Input  | 65534 | 9830  |')
        self._rsl_e1240.append('// | Analog Output | 4095  | 615   |')
        self._rsl_e1240.append('// | RTD example   | 1500  | -50   |')
        self._rsl_e1240.append('// ---------------------------------')
        self._rsl_e1240.append("")
        # channels
        channels = self.__slot['channels']
        channel_list = list(channels.keys())
        channel_list.sort()
        for channel_number in channel_list:
            channel = channels[channel_number]
            cn = int(channel_number)
            tag_name = channel['tag_name']
            scaling_dict = channel['scaling']
            if not tag_name:
                self._rsl_e1240.append(f'// Channel {cn} - Spare')
                self._rsl_e1240.append('// Ensure fault bit is not set')
                self._rsl_e1240.append(f'{self.rack__slot}_unreliable.{cn} := 0;')
                self._rsl_e1240.append('// Ensure manual bit is not set')
                self._rsl_e1240.append(f'{self.rack__slot}_manual.{cn} := 0;')
            else:
                self._rsl_e1240.append(f'// Channel {cn} - {tag_name}')
                self._rsl_e1240.append(
                    '// Copy the bits from the input INT to an intermediate DINT to account for Unsigned INT which AB does not do')
                self._rsl_e1240.append(
                    f'{self.rack__slot}_btdt_c{cn:02}.Source := {self.rack__slot}_moxa_{self.slot_type}:I.Data[{channel_number}];')
                self._rsl_e1240.append(f'{self.rack__slot}_btdt_c{cn:02}.SourceBit := 0;')
                self._rsl_e1240.append(f'{self.rack__slot}_btdt_c{cn:02}.Length := 16; ')
                self._rsl_e1240.append(f'{self.rack__slot}_btdt_c{cn:02}.DestBit := 0;')
                self._rsl_e1240.append(f'{self.rack__slot}_btdt_c{cn:02}.Target := zero;')
                self._rsl_e1240.append(f'BTDT({self.rack__slot}_btdt_c{cn:02});')
                self._rsl_e1240.append(f'{self.rack__slot}c{cn:02} := {self.rack__slot}_btdt_c{cn:02}.Dest;')
                self._rsl_e1240.append('// Process the AOI')
                self._rsl_e1240.append(f'AOI_AI(aoi_{self.rack__slot}c{cn:02}, {self.rack__slot}c{cn:02}, {tag_name});')
                self._rsl_e1240.append('// Set the channel min/max raw and engineering scaling.')
                self._rsl_e1240.append(f"{tag_name}.Scale.RawMax := {scaling_dict['raw_max']};")
                self._rsl_e1240.append(f"{tag_name}.Scale.RawMin := {scaling_dict['raw_min']};")
                self._rsl_e1240.append(f"{tag_name}.Scale.EUMax := {scaling_dict['eu_max']};")
                self._rsl_e1240.append(f"{tag_name}.Scale.EUMin := {scaling_dict['eu_min']};")
                self._rsl_e1240.append(f"{tag_name}.Scale.Scale_Input_Using_Counts := {scaling_dict['use_counts']};")
                self._rsl_e1240.append('// Set the channel fault limits and the bit in the unreliable DINT')
                self._rsl_e1240.append(f'{tag_name}.Fault.Program_Input_Hi := 65534;')
                self._rsl_e1240.append(f'{tag_name}.Fault.Program_Input_Lo := 9830;')
                self._rsl_e1240.append(f'{self.rack__slot}_unreliable.{cn} := {tag_name}.Fault.Fault;')
                self._rsl_e1240.append('// Set the channel in manual bit in the manual DINT')
                self._rsl_e1240.append(f'{self.rack__slot}_manual.{cn} := {tag_name}.Manual;')
            self._rsl_e1240.append("")

    @property
    def rack__slot_e1240_list(self):
        return self._rsl_e1240

    @rack__slot_e1240_list.setter
    def rack__slot_e1240_list(self, rsl_e1240):
        self._rsl_e1240 = rsl_e1240


class MoxaE1241(MoxaE1200):
    def __init__(self, rack_num, slot_num, slot_type, slot):
        super(MoxaE1241, self).__init__(rack_num, slot_num, slot_type)
        self.__slot = slot
        self._rsl_e1241 = [f'// Moxa Digital Inputs and Outputs E1241']
        self._rsl_e1241.extend(self.comm_config)
        # channels
        channels = self.__slot['channels']
        channel_list = list(channels.keys())
        channel_list.sort()
        for channel_number in channel_list:
            channel = channels[channel_number]
            cn = int(channel_number)
            tag_name = channel['tag_name']
            if not tag_name:
                self._rsl_e1241.append(f'// Channel {cn} - Spare')
            else:
                self._rsl_e1241.append(f'// Channel {cn} - {tag_name}')
                self._rsl_e1241.append('// Process the AOI')
                self._rsl_e1241.append(f'AOI_AO(aoi_{self.rack__slot}c{cn:02}, {self.rack__slot}c{cn:02}, {tag_name});')
                self._rsl_e1241.append(
                    '// Copy the bits from the intermediate DINT to the output unsigned INT to account for '
                    'Unsigned INT which AB does not do')
                self._rsl_e1241.append(f'{self.rack__slot}_btdt_c{cn:02}.Source := {self.rack__slot}c{cn:02};')
                self._rsl_e1241.append(f'{self.rack__slot}_btdt_c00.SourceBit := 0;')
                self._rsl_e1241.append(f'{self.rack__slot}_btdt_c{cn:02}.Length := 16;')
                self._rsl_e1241.append(f'{self.rack__slot}_btdt_c{cn:02}.DestBit := 0;')
                self._rsl_e1241.append(f'{self.rack__slot}_btdt_c{cn:02}.Target := zero;')
                self._rsl_e1241.append(f'BTDT({self.rack__slot}_btdt_c{cn:02});')
                self._rsl_e1241.append(
                    f'{self.rack__slot}_moxa_{self.slot_type}:O.Data[{cn}] := {self.rack__slot}_btdt_c{cn:02}.Dest;')
            self._rsl_e1241.append(" ")

    @property
    def rack__slot_e1241_list(self):
        return self._rsl_e1241

    @rack__slot_e1241_list.setter
    def rack__slot_e1241_list(self, rsl_e1241):
        self._rsl_e1241 = rsl_e1241


class MoxaE1260(MoxaE1200):
    def __init__(self, rack_num, slot_num, slot_type, slot):
        super(MoxaE1260, self).__init__(rack_num, slot_num, slot_type)
        self.__slot = slot
        self._rsl_e1260 = [f'// Moxa RTD Analog Inputs E1260']
        # A call to the parent property member which holds the communication settings.
        self._rsl_e1260.extend(self.comm_config)
        # A call to the clear_unused_bits_analog parent method.
        self._rsl_e1260.extend(self.clear_unused_bits_analog())
        self._rsl_e1260.append('// The raw low and high for an analog input/output is based on a 0-20ma signal.')
        self._rsl_e1260.append("/*\n"
                               "   The low and high for an rtd will be based on the raw side which comes in one decimal to the\n"
                               "   right to large. If for example a value above 150 or below -5 deg F should cause a fault, then on the raw side\n "
                               "  you would set the [tag].Fault.Program_Input_Hi = 1500 and [tag].Fault.Program_Input_Lo = -50\n"
                               "*/")
        self._rsl_e1260.append('// ---------------------------------')
        self._rsl_e1260.append('// | Signal        | High  | Low   |')
        self._rsl_e1260.append('// | ------------- |-------|-------|')
        self._rsl_e1260.append('// | Analog Input  | 65534 | 9830  |')
        self._rsl_e1260.append('// | Analog Output | 4095  | 615   |')
        self._rsl_e1260.append('// | RTD example   | 1500  | -50   |')
        self._rsl_e1260.append('// ---------------------------------')
        self._rsl_e1260.append("")
        # channels
        channels = self.__slot['channels']
        channel_list = list(channels.keys())
        channel_list.sort()
        for channel_number in channel_list:
            channel = channels[channel_number]
            cn = int(channel_number)
            tag_name = channel['tag_name']
            scaling_dict = channel['scaling']
            if not tag_name:
                self._rsl_e1260.append(f'// Channel {cn} - Spare')
                self._rsl_e1260.append('// Ensure fault bit is not set')
                self._rsl_e1260.append(f'{self.rack__slot}_unreliable.{cn} := 0;')
                self._rsl_e1260.append('// Ensure manual bit is not set')
                self._rsl_e1260.append(f'{self.rack__slot}_manual.{cn} := 0;')
            else:
                self._rsl_e1260.append(f'// Channel {cn} - {tag_name}')
                self._rsl_e1260.append(
                    f'{self.rack__slot}c{cn:02} := {self.rack__slot}_moxa_{self.slot_type}:I.Data[{channel_number}];')
                # if we are using jci nickel then uncomment the next two lines
                # self._rsl_e1260.append('// convert jci nickel to degrees f - rescaled to c in ai')
                # self._rsl_e1260.append(f'AOI_JCI_Nickel(aoi_{self.rack__slot}c{cn:02}_jci, {self.rack__slot}c{cn:02}r, {self.rack__slot}c{cn:02}f, JCI_Nickel_RTD);')
                self._rsl_e1260.append('// Process the AOI')
                # if using jci nickel use the next line. if not use the line after
                # self._rsl_e1260.append(f'AOI_AI(aoi_{self.rack__slot}c{cn:02}, {self.rack__slot}c{cn:02}f, {tag_name});')
                self._rsl_e1260.append(f'AOI_AI(aoi_{self.rack__slot}c{cn:02}, {self.rack__slot}c{cn:02}, {tag_name});')
                self._rsl_e1260.append('// Set the channel min/max raw and engineering scaling.')
                self._rsl_e1260.append(f"{tag_name}.Scale.RawMax := {scaling_dict['raw_max']};")
                self._rsl_e1260.append(f"{tag_name}.Scale.RawMin := {scaling_dict['raw_min']};")
                self._rsl_e1260.append(f"{tag_name}.Scale.EUMax := {scaling_dict['eu_max']};")
                self._rsl_e1260.append(f"{tag_name}.Scale.EUMin := {scaling_dict['eu_min']};")
                self._rsl_e1260.append(f"{tag_name}.Scale.Scale_Input_Using_Counts := {scaling_dict['use_counts']};")
                self._rsl_e1260.append('// Set the channel fault limits and the bit in the unreliable DINT')
                self._rsl_e1260.append(f'{tag_name}.Fault.Program_Input_Hi := 65534;')
                self._rsl_e1260.append(f'{tag_name}.Fault.Program_Input_Lo := 9830;')
                self._rsl_e1260.append(f'{self.rack__slot}_unreliable.{cn} := {tag_name}.Fault.Fault;')
                self._rsl_e1260.append('// Set the channel in manual bit in the manual DINT')
                self._rsl_e1260.append(f'{self.rack__slot}_manual.{cn} := {tag_name}.Manual;')
            self._rsl_e1260.append("")

    @property
    def rack__slot_e1260_list(self):
        return self._rsl_e1260

    @rack__slot_e1260_list.setter
    def rack__slot_e1260_list(self, rsl_e1260):
        self._rsl_e1260 = rsl_e1260
