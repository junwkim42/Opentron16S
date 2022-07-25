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

    #Pipette and pipette tips
    small_tip = 'p20_single_gen2'
    big_tip = 'p_300_multi_gen2'
    s_tips = [protocol.load_labware('opentrons_96_filtertiprack_20ul', '4')]
    p300tips = [protocol.load_labware('opentrons_96_filtertiprack_200ul', '5')]

    p20 = protocol.load_instrument(small_tip, 'left', tip_racks=s_tips)
    p300 = protocol.load_instrument(big_tip, 'right', tip_racks=p300tips)

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

    
    # Well Setup
    tc_samps = reaction_plate.columns_by_name()
    mag_cols = mag_plate.columns_by_name()
    norm2_wells = [reaction_plate.wells_by_name()[idx] for idx in ['B9', 'C9', 'D9', 'E9', 'F9', 'G9']]
    norm_stop_wells =[reaction_plate.wells_by_name()[idx] for idx in ['B10', 'C10', 'D10', 'E10', 'F10', 'G10']]


    library_mag = mag_cols['7'] + mag_cols['8']
    library_300 = [mag_cols['7'][0], mag_cols['8'][0]]

    norm1_tc = tc_samps['7'] + tc_samps['8']
    norm1_tc_300 = [tc_samps['7'][0], tc_samps['8'][0]]
    norm1_reserve_mag = [mag_cols['9'][0], mag_cols['10'][0]]
 

    #Distribute 5ul of Normalase I master mix to libraries in magnetic plate columns 7 and 8
    for well in library_mag:
        p20.pick_up_tip()
        p20.transfer(5, normalase1_mm.bottom(0.2), well.bottom(1))
        p20.blow_out(well.top(-2))
        p20.mix(3, 15, well.bottom(0.2))
        p20.blow_out(well.top(-2))
        p20.drop_tip()
    
    #Preheat thermocycler block to 30C
    thermocycler.set_block_temperature(30)

    #Transfer 25ul of mixed library to Thermocycler column 7 and 8
    for src, dest in zip(library_300, norm1_tc_300):
        p300.pick_up_tip()
        p300.aspirate(30, src.bottom(0.2))
        p300.dispense(40, dest.bottom(2))
        p300.blow_out(dest.top(-5))
        p300.drop_tip()
    
    #Hold at 30C for 15mins
    thermocycler.set_block_temperature(30, hold_time_minutes=15)
    thermocycler.set_block_temperature(4)

    #Transfer 5ul of Normalase I samples into temporary pool A6 of Temperature module
    #Transfer rest to Column 9 and 10 of magnetic module for future repeated experiment. (4 weeks lifetime)
    for well in norm1_tc:
        p20.pick_up_tip()
        p20.transfer(5, well.bottom(0.2), tmp_pool.bottom(1))
        p20.blow_out(tmp_pool.top(-5))
        p20.drop_tip() 

    for src, dest in zip(norm1_tc_300, norm1_reserve_mag):
        p300.pick_up_tip()
        p300.transfer(30, src.bottom(0.2), dest.bottom(1))
        p300.blow_out(dest.top(-5))
        p300.drop_tip()

    #Transfer 16ul (1ul per sample) of Normalase II mastermix to the temporary pool and mix
    p20.flow_rate.aspirate = 7.56
    p20.flow_rate.dispense = 7.56
    p20.pick_up_tip()
    p20.transfer(16, normalase2_mm.bottom(0.2), tmp_pool.bottom(1))
    p20.mix(5,20, tmp_pool.bottom(1))
    p20.blow_out(tmp_pool.top(-5))
    p20.drop_tip()

    #Preheat thermocycler module to 37C for Normalase II
    thermocycler.set_block_temperature(37)
    #Distribute 16ul of mixed sample to 5 wells of Thermocycler in column 9
    for well in norm2_wells:
        p20.pick_up_tip()
        p20.transfer(16, tmp_pool.bottom(0.2), well.bottom(1))
        p20.blow_out(well.top(-5))
        p20.drop_tip() 
    
    #Hold at 37C for 15mins
    thermocycler.set_block_temperature(37, hold_time_minutes=15)
    thermocycler.set_block_temperature(4)

    #Transfer to reagent X1 in B6 of temperature module 
    for well in norm2_wells:
        p20.pick_up_tip()
        p20.transfer(17, well.bottom(0.2), x1_reagent.bottom(1))
        p20.blow_out(x1_reagent.top(-5))
        p20.drop_tip() 
    
    #mix
    p20.pick_up_tip()
    p20.mix(3, 15, x1_reagent.bottom(0.2))
    p20.blow_out(x1_reagent.top(-2))

    #Preheat thermocycler block and lid to 95C for Normalase inactivation
    thermocycler.set_block_temperature(95)
    thermocycler.set_lid_temperature(95)
    
    #Distribute 17 ul of mixed sample to 5 wells of thermocycler in column 10
    for well in norm_stop_wells:
        p20.pick_up_tip()
        p20.transfer(17, x1_reagent.bottom(0.2), well.bottom(1))
        p20.blow_out(well.top(-5))
        p20.drop_tip()

    #Hold at 95C for 2mins
    thermocycler.close_lid()
    thermocycler.set_block_temperature(95, hold_time_minutes=2)
    thermocycler.open_lid()
    thermocycler.set_block_temperature(4)

    #Pool libraries into final pool, C6 of Temperature module
    for well in norm_stop_wells:
        p20.pick_up_tip()
        p20.transfer(20, well.bottom(0.2), final_pool.bottom(1))
        p20.blow_out(final_pool.top(-5))
        p20.drop_tip() 

    protocol.comment('Swift SNAP 16S Normalase complete. Normalized pool : C6 of temperature module. N1 Libraries : Column 9 and 10 of Magnetic module.')
