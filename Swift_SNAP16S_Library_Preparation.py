metadata = {
    'protocolName': '',
    'author': 'Junwon Kim <junwon.kim@uconn.edu>',
    'source': 'Protocol Library',
    'apiLevel': '2.3'
}

def run(protocol):
    #Load run variables
    #Number of samples
    no_samps = 16 #designed for 16 samples.
    no_pcr_cycle_1 = 4
    no_pcr_cycle_2 = 14
    barcode_pcr_cycle = 7

    #Pipette and pipette tips
    small_tip = 'p20_single_gen2'
    big_tip = 'p_300_multi_gen2'
    s_tips = [protocol.load_labware('opentrons_96_filtertiprack_20ul', '4')]
    p300tips = [protocol.load_labware('opentrons_96_filtertiprack_200ul', i) for i in ['5','6','9']]

    p20 = protocol.load_instrument(small_tip, 'left', tip_racks=s_tips)
    p300 = protocol.load_instrument(big_tip, 'right', tip_racks=p300tips)

    #Reservoir 
    rt_reagents = protocol.load_labware('nest_12_reservoir_15ml', '2')

    #Modules: Magnetic, Temperature with 24 well aluminum block and Thermocycler
    magdeck = protocol.load_module('magnetic module gen2', '1')
    mag_plate = magdeck.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')

    tempdeck = protocol.load_module('temperature module gen2', '3')
    cool_reagents = tempdeck.load_labware('opentrons_24_aluminumblock_generic_2ml_screwcap')

    thermocycler = protocol.load_module('thermocycler')
    reaction_plate = thermocycler.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')

    # Reagent Setup
    #PEG_NaCL is not used in this protocol due to "off-bead PCR" performed in this protocol
    pcr_mm = cool_reagents.wells_by_name()['A1']
    index_mm = cool_reagents.wells_by_name()['A2']
    normalase1_mm = cool_reagents.wells_by_name()['A3']
    normalase2_mm = cool_reagents.wells_by_name()['A4']
    post_pcr_buffer = cool_reagents.wells_by_name()['A5']
    tmp_pool = cool_reagents.wells_by_name()['A6']
    x1_reagent = cool_reagents.wells_by_name()['B6']
    final_pool = cool_reagents.wells_by_name()['C6']
    peg_nacl = rt_reagents.wells_by_name()['A2']
    beads = rt_reagents.wells_by_name()['A4']
    ethanol = rt_reagents.wells_by_name()['A6']
    ethanol_2 = rt_reagents.wells_by_name()['A7']
    
    # Well Setup
    tc_samps = reaction_plate.columns_by_name()
    mag_cols = mag_plate.columns_by_name()

    pcr_prep_samples = mag_cols['1'] + mag_cols['2']
    pcr_300 = [mag_cols['1'][0], mag_cols['2'][0]]
    pcr_300_thermo = [tc_samps['1'][0], tc_samps['2'][0]]
    cleanup_mag = mag_cols['3'] + mag_cols['4']
    cleanup_300_mag = [mag_cols['3'][0], mag_cols['4'][0]]
    cleanup_2_300_mag = [mag_cols['5'][0], mag_cols['6'][0]]

    index_prep_samples = tc_samps['5'] + tc_samps['6']
    index_300 = [tc_samps['5'][0], tc_samps['6'][0]]

    library_300 = [mag_cols['7'][0], mag_cols['8'][0]]

    waste = rt_reagents.wells_by_name()['A11']
    waste_2 = rt_reagents.wells_by_name()['A12']

    #Multiplex PCR Step
    #Transfer 20ul pcr mastermix from Temp A1 to Mag columns 1 and 2
    for well in pcr_prep_samples:
        p20.pick_up_tip()
        p20.transfer(20, pcr_mm.bottom(0.2), well)
        p20.blow_out()
        p20.drop_tip()

    #Preheat thermocycler lid and block to 105C and 98C respectively
    thermocycler.set_lid_temperature(105)
    thermocycler.set_block_temperature(98)
    
    for src, dest in zip(pcr_300, pcr_300_thermo):
        p300.pick_up_tip()
        p300.transfer(40, src.bottom(0.2), dest)
        p20.blow_out()
        p20.drop_tip()

    thermocycler.close_lid()
    #Multiplex pcr cycles as indicated in the manual
    pcr_cycle_1 = [
        {'temperature': 98, 'hold_time_seconds': 10},
        {'temperature': 63, 'hold_time_seconds': 300},
        {'temperature': 65, 'hold_time_seconds': 60}
        ]
    pcr_cycle_2 = [
        {'temperature': 98, 'hold_time_seconds': 10},
        {'temperature': 64, 'hold_time_seconds': 60}
        ]
    
    thermocycler.set_block_temperature(98, hold_time_seconds=30)
    thermocycler.execute_profile(steps=pcr_cycle_1, repetitions=no_pcr_cycle_1)
    thermocycler.execute_profile(steps=pcr_cycle_2, repetitions=no_pcr_cycle_2)
    thermocycler.set_block_temperature(65, hold_time_seconds=60)
    thermocycler.set_block_temperature(4)
    thermocycler.open_lid()
    thermocycler.set_lid_temperature(32)

    #Cleanup 1
    #Transfer from Thermocycler Column 1 and 2 to Magnetic column 3 and 4 for cleanup
    for src, dest in zip(pcr_300_thermo, cleanup_300_mag):
        p300.pick_up_tip()
        p300.transfer(40, src.bottom(0.2), dest)    
        p300.blow_out()
        p300.drop_tip()    

    #Mix beads before distribution
    p300.pick_up_tip()
    p300.mix(5, 150, beads.bottom(2))
    #Distribute 30ul beads to Magnetic colum 3 and 4 and mix
    for dest in cleanup_300_mag:
        if not p300.hw_pipette['has_tip']:
            p300.pick_up_tip()
        p300.aspirate(30, beads.bottom(1))
        p300.air_gap(10)
        p300.flow_rate.aspirate = 50
        p300.flow_rate.dispense = 50
        p300.dispense(40, dest)
        p300.mix(3, 50, dest.bottom(2))
        p300.blow_out(dest.top(-3))
        p300.drop_tip()
        p300.flow_rate.aspirate = 94
        p300.flow_rate.dispense = 94

    #Incubate for 5 minutes and activate magnetic module for 5 minutes
    protocol.delay(minutes=5)
    magdeck.engage()
    protocol.delay(minutes=5)

    #Discard supernatant into Reservoir well 11
    p300.flow_rate.aspirate = 24
    for mag_samp in cleanup_300_mag:
        p300.pick_up_tip()
        p300.aspirate(60, mag_samp.bottom(1))
        p300.dispense(70, waste.bottom(2))
        p300.blow_out(waste.top(-5))
        p300.drop_tip()

    #Transfer 95ul of 80% EtOH from the reservoir to Column 3 and 4 of magnetic module
    #Aspirate and discard EtOH after 30 seconds of contact. Repeat twice
    for _ in range(2):
        p300.flow_rate.aspirate = 94
        for mag_samp in cleanup_300_mag:
            p300.pick_up_tip()
            p300.aspirate(95, ethanol.bottom(2))
            p300.air_gap(20)
            p300.dispense(120, mag_samp.top(-2))
            p300.blow_out(mag_samp.top())
            p300.drop_tip()    
        protocol.delay(seconds=30)    
        p300.flow_rate.aspirate = 24
        for mag_samp in cleanup_300_mag:
            p300.pick_up_tip()
            p300.aspirate(110, mag_samp.bottom(0.2))
            p300.air_gap(20)
            p300.dispense(130, waste_2.bottom(2))
            p300.blow_out(waste_2.top())
            p300.drop_tip()
    p300.flow_rate.aspirate = 94
    #EtOH dry time 3 minutes
    protocol.delay(minutes=3)

    #Resuspend pellets to 17.4ul Post PCR TE buffer
    magdeck.disengage()
    for well in cleanup_mag:
        p20.pick_up_tip()
        p20.transfer(17.4, post_pcr_buffer.bottom(0.2), well.bottom(1))
        p20.mix(3, 15, well.bottom(0.2))
        p20.blow_out(well.top(-5))
        p20.drop_tip()

    #Incubate for 5 minutes and activate magnetic module for 5 minutes
    protocol.delay(minutes=5)
    magdeck.engage()
    protocol.delay(minutes=5)

    #Set block temperature to 37C and lid temperature to 105
    thermocycler.set_lid_temperature(105)
    thermocycler.set_block_temperature(37)

    #Transfer clean 17.4 of elute to column 5 and 6 of Thermocycler
    #Should be pre loaded with 3.7ul of pre-mixed SNAP UDI or 2ul SNAP CD Index D50X + 1.7 ul SNAP CD Index S7XX
    for src, dest in zip(cleanup_mag, index_prep_samples):
        p20.pick_up_tip()
        p20.transfer(17.4, src.bottom(0.2), dest.bottom(3))
        p20.blow_out(dest.top(-5))
        p20.drop_tip()
    magdeck.disengage()
    #Transfer Index mastermix to column 5 and 6 of Thermocycler
    #Transfer 20 ul + 8.9 ul
    p20.flow_rate.aspirate = 7.56
    p20.flow_rate.dispense = 7.56
    for well in index_prep_samples:
        p20.pick_up_tip()
        p20.transfer(20, index_mm.bottom(0.2), well.bottom(3))
        p20.blow_out(well.top(-5))
        p20.drop_tip()
    for well in index_prep_samples:
        p20.pick_up_tip()
        p20.transfer(8.9, index_mm.bottom(0.2), well.bottom(3))
        p20.blow_out(well.top(-5))
        p20.drop_tip()
    
    p20.flow_rate.aspirate = 3.78
    p20.flow_rate.dispense = 3.78

    #Index cycles
    Index_cycle = [
        {'temperature': 98, 'hold_time_seconds': 10},
        {'temperature': 60, 'hold_time_seconds': 30},
        {'temperature': 66, 'hold_time_seconds': 60}
        ]
    
    thermocycler.close_lid()

    # Hold at 37C 20 minutes and 98C 30 sec
    thermocycler.set_block_temperature(37, hold_time_seconds=1200)
    thermocycler.set_block_temperature(98, hold_time_seconds=30)
    # Loop through PCR cycles profile for 20 cycles
    thermocycler.execute_profile(steps=Index_cycle, repetitions=barcode_pcr_cycle)

    # Set Post-pcr temp
    thermocycler.set_block_temperature(4)
    thermocycler.open_lid()
    thermocycler.set_lid_temperature(32)

    #Transfer indexed samples to column 5 and 6 of magnetic module for cleanup
    for src, dest in zip(index_300, cleanup_2_300_mag):
        p300.pick_up_tip()
        p300.transfer(60, src.bottom(0.2), dest.bottom(1))
        p300.blow_out(dest.top(-5))
        p300.drop_tip()

    #Cleanup2
    #Mix beads before distribution
    p300.pick_up_tip()
    p300.mix(5, 150, beads.bottom(2))
    #Distribute 42.5ul beads to Magnetic colum 3 and 4 and mix
    for dest in cleanup_2_300_mag:
        if not p300.hw_pipette['has_tip']:
            p300.pick_up_tip()
        p300.aspirate(42.5, beads.bottom(1))
        p300.air_gap(10)
        p300.flow_rate.aspirate = 50
        p300.flow_rate.dispense = 50
        p300.dispense(60, dest)
        p300.mix(3, 50, dest.bottom(2))
        p300.blow_out(dest.top(-3))
        p300.drop_tip()
        p300.flow_rate.aspirate = 94
        p300.flow_rate.dispense = 94

    #Incubate for 5 minutes and activate magnetic module for 5 minutes
    protocol.delay(minutes=5)
    magdeck.engage()
    protocol.delay(minutes=5)

    #Discard supernatant into Reservoir well 11
    p300.flow_rate.aspirate = 24
    for mag_samp in cleanup_2_300_mag:
        p300.pick_up_tip()
        p300.aspirate(60, mag_samp.bottom(1))
        p300.dispense(70, waste.bottom(2))
        p300.blow_out(waste.top(-5))
        p300.drop_tip()

    #Transfer 95ul of 80% EtOH from the reservoir to Column 3 and 4 of magnetic module
    #Aspirate and discard EtOH after 30 seconds of contact. Repeat twice
    for _ in range(2):
        p300.flow_rate.aspirate = 94
        for mag_samp in cleanup_2_300_mag:
            p300.pick_up_tip()
            p300.aspirate(95, ethanol_2.bottom(2))
            p300.air_gap(20)
            p300.dispense(120, mag_samp.top(-2))
            p300.blow_out(mag_samp.top())
            p300.drop_tip()    
        protocol.delay(seconds=30)    
        p300.flow_rate.aspirate = 24
        for mag_samp in cleanup_2_300_mag:
            p300.pick_up_tip()
            p300.aspirate(110, mag_samp.bottom(0.2))
            p300.air_gap(20)
            p300.dispense(130, waste_2.bottom(2))
            p300.blow_out(waste_2.top())
            p300.drop_tip()
    p300.flow_rate.aspirate = 94
    #EtOH dry time 3 minutes
    protocol.delay(minutes=3)

    #Resuspend pellets to 20ul Post PCR TE buffer
    magdeck.disengage()
    for well in cleanup_mag:
        p20.pick_up_tip()
        p20.transfer(20, post_pcr_buffer.bottom(0.2), well.bottom(1))
        p20.mix(3, 15, well.bottom(0.2))
        p20.blow_out(well.top(-5))
        p20.drop_tip()

    #Incubate for 5 minutes and activate magnetic module for 5 minutes
    protocol.delay(minutes=5)
    magdeck.engage()
    protocol.delay(minutes=5)

    #transfer clean eluates to Column 7 and 8 of magnetic module
    p300.flow_rate.aspirate = 24
    for src, dest in zip(cleanup_2_300_mag, library_300):
        p300.pick_up_tip()
        p300.aspirate(30, src.bottom(0.2))
        p300.dispense(40, dest.bottom(1))
        p300.blow_out(dest.top(-5))
        p300.drop_tip()


    #End of protocol. Turn off Thermocycler and Temperature module in the Opentrons App or manually
    magdeck.disengage()
    protocol.comment('Swift SNAP 16S library preparation complete. Libraries : Column 7 and 8.')
    protocol.comment('You can proceed to Swift Normalase protocol or normalize the libraries manually. However, library quantification is strongly recommended')

