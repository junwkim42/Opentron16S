metadata = {
    'protocolName': '',
    'author': 'Junwon Kim <junwon.kim@uconn.edu>',
    'source': 'Protocol Library',
    'apiLevel': '2.3'
}

def run(protocol):
    #Load run variables
    #Number of samples
    no_samps = 16 #Designed for 16 samples.
    amp_pcr_cycle = 20
    barcode_pcr_cycle = 5

    #Pipette and pipette tips
    small_tip = 'p20_single_gen2'
    big_tip = 'p_300_multi_gen2'
    s_tips = [protocol.load_labware('opentrons_96_filtertiprack_20ul', i) for i in ['4', '5']]
    p300tips = [protocol.load_labware('opentrons_96_filtertiprack_200ul', '9')]

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
    amplification_mm = cool_reagents.wells_by_name()['A1']
    cleanup_mm = cool_reagents.wells_by_name()['A2']
    index_mm = cool_reagents.wells_by_name()['A3']
    beads = cool_reagents.wells_by_name()['A4']
    water = cool_reagents.wells_by_name()['A5']
    ethanol = rt_reagents.wells_by_name()['A2']
    waste = rt_reagents.wells_by_name()['A11']
    waste_2 = rt_reagents.wells_by_name()['A12']
    
    # Well Setup
    tc_samps = reaction_plate.columns_by_name()
    mag_cols = mag_plate.columns_by_name()

    amplification_prep_samples = tc_samps['1'] + tc_samps['2']
    index_prep_samples = tc_samps['5'] + tc_samps['6']
    mag_reserve = mag_cols['1'] + mag_cols['2']
    mag_clean = mag_cols['5'] + mag_cols['6']
    mag_clean_300 = [mag_cols['5'][0], mag_cols['6'][0]]
    mag_final = mag_cols['9'] + mag_cols['10']


    # Actively cool the samples and enzymes
    tempdeck.set_temperature(4)
    thermocycler.set_block_temperature(4)

    #Transfer 18 ul of Amplification mastermix from A1 of temperature module to
    #column 1 and 2 of 96 well pcr plate on thermocycler module
    for well in amplification_prep_samples:
        p20.pick_up_tip()
        p20.transfer(18, amplification_mm.bottom(0.2), well)
        p20.blow_out()
        p20.drop_tip()

    #Target Sequence Amplification PCR cycles
    TSA_cycle = [
        {'temperature': 95, 'hold_time_seconds': 30},
        {'temperature': 55, 'hold_time_seconds': 30},
        {'temperature': 72, 'hold_time_seconds': 180}
        ]
    
    # Set thermocycler lid temperature
    thermocycler.set_lid_temperature(105)
    thermocycler.close_lid()

    # Hold at 95C 10 minutes
    thermocycler.set_block_temperature(95, hold_time_seconds=600)

    # Loop through PCR cycles profile for 20 cycles
    thermocycler.execute_profile(steps=TSA_cycle, repetitions=amp_pcr_cycle)

    # Set Post-pcr temp
    thermocycler.set_block_temperature(4)
    thermocycler.open_lid()
    thermocycler.set_lid_temperature(32)

    #Transfer 1ul of clean-up solution from A2 of temperature module to
    #column 1 and 2 of 96 well pcr plate on thermocycler module
    for well in amplification_prep_samples:
        p20.pick_up_tip()
        p20.transfer(1, cleanup_mm.bottom(0.2), well)
        p20.blow_out()
        p20.drop_tip()

    # Set thermocycler lid temperature
    thermocycler.set_lid_temperature(105)
    thermocycler.close_lid()

    # Hold at 37C for 15 minutes, then hold at 95C for 10 minutes
    thermocycler.set_block_temperature(37, hold_time_seconds=900)
    thermocycler.set_block_temperature(95, hold_time_seconds=600)

    # Set post-pcr temp
    thermocycler.set_block_temperature(4)
    thermocycler.open_lid()

    #Transfer 14ul of index master mix to column 5 and 6 of thermocycler module
    #column 5 and 6 are loaded with 4ul of index primers
    for well in index_prep_samples:
        p20.pick_up_tip()
        p20.transfer(14, index_mm.bottom(0.2), well)
        p20.blow_out()
        p20.drop_tip()

    #Transfer 2ul of amplified and cleaned samples in column 1 and 2 to 5 and 6 of thermocycler module
    for samp, index in zip(amplification_prep_samples, index_prep_samples):
        p20.pick_up_tip()
        p20.transfer(2, samp, index)
        p20.blow_out()
        p20.drop_tip()

    #Transfer rest of the amplified samples to column 1 and 2 of magnetic module
    for mag, thermo in zip(mag_reserve, amplification_prep_samples):
        p20.pick_up_tip()
        p20.transfer(20, thermo, mag)
        p20.blow_out()
        p20.drop_tip()

    #Barcode Addition PCR cycles
    BA_cycle = [
        {'temperature': 95, 'hold_time_seconds': 30},
        {'temperature': 55, 'hold_time_seconds': 30},
        {'temperature': 72, 'hold_time_seconds': 180}
        ]
    # Set thermocycler lid temperature
    thermocycler.set_lid_temperature(105)
    thermocycler.close_lid()

    # Hold at 95C 10 minutes
    thermocycler.set_block_temperature(95, hold_time_seconds=600)

    # Loop through PCR cycles profile for 20 cycles
    thermocycler.execute_profile(steps=BA_cycle, repetitions=barcode_pcr_cycle)

    # Set Post-pcr temp
    thermocycler.set_block_temperature(4)
    thermocycler.open_lid()
    thermocycler.set_lid_temperature(32)

    #Transfer indexed sample to magnetic module column 5 and 6 for bead clean-up
    for idx, mag in zip(index_prep_samples, mag_clean):
        p20.pick_up_tip()
        p20.transfer(20, idx, mag)
        p20.blow_out()
        p20.drop_tip()
    #mix beads before distribution
    p20.pick_up_tip()
    p20.mix(5, 18, beads.bottom(2))
    p20.drop_tip()
    #Transfer 16 ul of bead to each sample from A4 of the temperature module to each well and mix
    for mag in mag_clean:
        p20.pick_up_tip()
        p20.transfer(16, beads.bottom(0.5), mag)
        p20.mix(3, 15, mag.bottom(0.2))
        p20.blow_out(mag.top())
        p20.drop_tip()

    #Incubate for 5 minutes and activate magnetic module for 10 minutes
    protocol.delay(minutes=5)
    magdeck.engage()
    protocol.delay(minutes=10)

    
    #Discard supernatant to Well 11 of reservoir
    p300.flow_rate.aspirate = 10
    for mag in mag_clean_300:
        p300.pick_up_tip()
        p300.aspirate(40, mag.bottom(0.5))
        p300.air_gap(20)
        p300.dispense(60, waste.bottom(2))
        p300.blow_out()
        p300.drop_tip()
    
    #Transfer 90ul of 80% EtOH from reservoir to column 5 and 6 of the magnetic plate.
    #Then, discard EtOH to Well 12 of reservoir. Repeat twice.
    p300.flow_rate.aspirate = 94
    for _ in range(2):
        for mag in mag_clean_300:
            p300.pick_up_tip()
            p300.aspirate(90, ethanol.bottom(1))
            p300.air_gap(20)
            p300.dispense(90, mag.top(-2))
            p300.blow_out(mag.top(3))
            #delay for 30sec
            protocol.delay(seconds=30)
        for mag in mag_clean_300:
            #discard to trash
            p300.aspirate(100, mag.bottom(0.5))
            p300.air_gap(20)
            p300.dispense(120, waste_2.bottom(2))
            p300.blow_out()
            p300.drop_tip()
    
    #Dry EtOH 2 minutes
    protocol.delay(minutes=3)
    #Deactivate magnet and transfer DNease/RNease free water
    magdeck.disengage()
    for mag in mag_clean:
        p20.pick_up_tip()
        p20.transfer(20, water.bottom(1), mag)
        p20.mix(5, 20, mag.bottom(0.5))
        p20.blow_out(mag.top(-5))
        p20.drop_tip()

    #Incubate for 5 minutes and activate magnetic module for 5 minutes
    protocol.delay(minutes=5)
    magdeck.engage()
    protocol.delay(minutes=5)
    #Transfer clean library to column 9 and 10
    for src, dest in zip(mag_clean, mag_final):
        p20.pick_up_tip()
        p20.transfer(20, src.bottom(0.2), dest.bottom(2))
        p20.blow_out(dest.top(-5))
        p20.drop_tip()

    #End of protocol. Turn off Thermocycler and Temperature module in the Opentrons App or manually
    magdeck.disengage()
    protocol.comment('Zymo Quick 16S library preparation complete. Libraries : Column 9 and 10. Amplified Samples : Column 1 and 2')