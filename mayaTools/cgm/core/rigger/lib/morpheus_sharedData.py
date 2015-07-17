_d_customizationGeoGroupsToCheck = {'body':'baseGeoGroup',
                                    'tongue':'tongueGeoGroup',
                                    'uprTeeth':'uprTeethGeoGroup',
                                    'lwrTeeth':'lwrTeethGeoGroup',
                                    'eyebrow':'eyebrowGeoGroup',
                                    'earLeft':'left_earGeoGroup',
                                    'earRight':'right_earGeoGroup',
                                    'eyeLeft':'left_eyeGeoGroup',
                                    'eyeRight':'right_eyeGeoGroup'}

#Data to assist in connecting blendshape channels to driver attrs on the face attr holder...
_l_facialRigBSNodes = ['brow_bsNode','cheek_bsNode','mouth_bsNode','lipsOutr_bsNode',
                       'lips_bsNode','nose_bsNode','jaw_bsNode','lipCenter_bsNode']#...blendshape nodes to check
_d_faceBlendshapeWiring = {'brow_center_dn':'',
                           'brow_center_up':'',
                           'brow_inr_dn_left':'lf_brow_inr_dn',
                           'brow_inr_dn_right':'rt_brow_inr_dn',
                           'brow_inr_up_left':'lf_brow_inr_up',
                           'brow_inr_up_right':'rt_brow_inr_up',
                           'brow_mid_dn_left':'lf_brow_mid_dn',
                           'brow_mid_dn_right':'rt_brow_mid_dn',
                           'brow_mid_up_left':'lf_brow_mid_up',
                           'brow_mid_up_right':'rt_brow_mid_up',
                           'brow_outr_dn_left':'lf_brow_outr_dn',
                           'brow_outr_dn_right':'rt_brow_outr_dn',
                           'brow_outr_up_left':'lf_brow_outr_up',
                           'brow_outr_up_right':'rt_brow_outr_up',
                           'brow_squeeze_left':'lf_brow_squeeze',
                           'brow_squeeze_right':'rt_brow_squeeze',
                           'cheek_blow_left':'lf_cheek_blow',
                           'cheek_blow_right':'rt_cheek_blow',
                           'cheek_dn_left':'lf_cheek_dn',
                           'cheek_dn_right':'rt_cheek_dn',
                           'cheek_suck_left':'lf_cheek_suck',
                           'cheek_suck_right':'rt_cheek_suck',
                           'cheek_up_left':'lf_cheek_up',
                           'cheek_up_right':'rt_cheek_up',
                           'eyeSqueeze_dn_left':'lf_eyeSqueeze_dn',
                           'eyeSqueeze_dn_right':'rt_eyeSqueeze_dn',
                           'eyeSqueeze_up_left':'lf_eyeSqueeze_up',
                           'eyeSqueeze_up_right':'rt_eyeSqueeze_up',
                           'mouth_back':'',
                           'mouth_dn':'',
                           'mouth_fwd':'',
                           'mouth_left':'',
                           'mouth_right':'',
                           'mouth_twist_left':'',
                           'mouth_twist_right':'',
                           'mouth_up':'',
                           'seal_center':['lf_lips_close_cntr','rt_lips_close_cntr'],
                           'seal_left':['lf_lips_close_outr'],
                           'seal_right':['rt_lips_close_outr'], 
                           'lips_frown_left':'lf_lips_frown',
                           'lips_frown_right':'rt_lips_frown',
                           'lips_narrow_left':'lf_lips_narrow',
                           'lips_narrow_right':'rt_lips_narrow',
                           'lips_out_left':'lf_lips_out',
                           'lips_out_right':'rt_lips_out',
                           'lips_purse_left':'lf_lips_purse',
                           'lips_purse_right':'rt_lips_purse',
                           'lips_smile_left':'lf_lips_smile',
                           'lips_smile_right':'rt_lips_smile',
                           'lips_twistDn_left':'lf_lips_twistDn',
                           'lips_twistDn_right':'rt_lips_twistDn',
                           'lips_twistUp_left':'lf_lips_twistUp',
                           'lips_twistUp_right':'rt_lips_twistUp',
                           'lips_wide_left':'lf_lips_wide',
                           'lips_wide_right':'rt_lips_wide',
                           'jDiff_dn_frown_left':'lf_jDiff_dn_frown',
                           'jDiff_dn_frown_right':'rt_jDiff_dn_frown',                           
                           'jDiff_dn_smile_left':'lf_jDiff_dn_smile',
                           'jDiff_dn_smile_right':'rt_jDiff_dn_smile', 
                           'nose_in_left':'lf_nose_in',
                           'nose_in_right':'rt_nose_in',
                           'nose_out_left':'lf_nose_out',
                           'nose_out_right':'rt_nose_out',
                           'nose_seal_up_cntr_left':'lf_nose_seal_up_cntr',
                           'nose_seal_up_cntr_right':'rt_nose_seal_up_cntr',
                           'nose_seal_up_outr_left':'lf_nose_seal_up_outr',
                           'nose_seal_up_outr_right':'rt_nose_seal_up_outr',
                           'nose_sneer_dn_left':'lf_nose_sneer_dn',
                           'nose_sneer_dn_right':'rt_nose_sneer_dn',
                           'nose_sneer_up_left':'lf_nose_sneer_up',
                           'nose_sneer_up_right':'rt_nose_sneer_up',
                           'jDiff_back_seal_cntr_left':'lf_jDiff_back_seal_cntr',
                           'jDiff_back_seal_cntr_right':'rt_jDiff_back_seal_cntr',
                           'jDiff_back_seal_outr_left':'lf_jDiff_back_seal_outr',
                           'jDiff_back_seal_outr_right':'rt_jDiff_back_seal_outr',
                           'jDiff_dn_seal_cntr_left':'lf_jDiff_dn_seal_cntr',
                           'jDiff_dn_seal_cntr_right':'rt_jDiff_dn_seal_cntr',
                           'jDiff_dn_seal_outr_left':'lf_jDiff_dn_seal_outr',
                           'jDiff_dn_seal_outr_right':'rt_jDiff_dn_seal_outr',
                           'jDiff_fwd_seal_cntr_left':'lf_jDiff_fwd_seal_cntr',
                           'jDiff_fwd_seal_cntr_right':'rt_jDiff_fwd_seal_cntr',
                           'jDiff_fwd_seal_outr_left':'lf_jDiff_fwd_seal_outr',
                           'jDiff_fwd_seal_outr_right':'rt_jDiff_fwd_seal_outr',
                           'jDiff_left_seal_cntr_left':'lf_jDiff_left_seal_cntr',
                           'jDiff_left_seal_cntr_right':'rt_jDiff_left_seal_cntr',
                           'jDiff_left_seal_outr_left':'lf_jDiff_left_seal_outr',
                           'jDiff_left_seal_outr_right':'rt_jDiff_left_seal_outr', 
                           'jDiff_right_seal_cntr_left':'lf_jDiff_right_seal_cntr',
                           'jDiff_right_seal_cntr_right':'rt_jDiff_right_seal_cntr',
                           'jDiff_right_seal_outr_left':'lf_jDiff_right_seal_outr',
                           'jDiff_right_seal_outr_right':'rt_jDiff_right_seal_outr',                           
                           'jaw_back':'',
                           'jaw_clench':'',
                           'jaw_dn':'',
                           'jaw_fwd':'',
                           'jaw_left':'',
                           'jaw_right':'',
                           'lipCntr_lwr_back':'lipLwr_center_bwd',
                           'lipCntr_lwr_dn_left':'lf_lipLwr_center_dn',
                           'lipCntr_lwr_dn_right':'rt_lipLwr_center_dn',
                           'lipCntr_lwr_fwd':'lipLwr_center_out',
                           'lipCntr_lwr_up_left':'lf_lipLwr_center_up',
                           'lipCntr_lwr_up_right':'rt_lipLwr_center_up',
                           'lipCntr_upr_back':'lipUpr_center_bwd',
                           'lipCntr_upr_dn_left':'lf_lipUpr_center_dn',
                           'lipCntr_upr_dn_right':'rt_lipUpr_center_dn',
                           'lipCntr_upr_fwd':'lipUpr_center_out',
                           'lipCntr_upr_up_left':'lf_lipUpr_center_up',
                           'lipCntr_upr_up_right':'rt_lipUpr_center_up',
                           'lipLwr_dn_left':'lf_lipLwr_dn',
                           'lipLwr_dn_right':'rt_lipLwr_dn',                         
                           'lipLwr_dnSeal_cntr_left':'lf_lipLwr_dnSeal_cntr',
                           'lipLwr_dnSeal_cntr_right':'rt_lipLwr_dnSeal_cntr',
                           'lipLwr_dnSeal_outr_left':'lf_lipLwr_dnSeal_outr',
                           'lipLwr_dnSeal_outr_right':'rt_lipLwr_dnSeal_outr',
                           'lipLwr_moreIn_left':'lf_lipLwr_moreIn',
                           'lipLwr_moreIn_right':'rt_lipLwr_moreIn',
                           'lipLwr_moreOut_left':'lf_lipLwr_moreOut',
                           'lipLwr_moreOut_right':'rt_lipLwr_moreOut',
                           'lipLwr_rollIn_left':'lf_lipLwr_rollIn',
                           'lipLwr_rollIn_right':'rt_lipLwr_rollIn',
                           'lipLwr_rollOut_left':'lf_lipLwr_rollOut',
                           'lipLwr_rollOut_right':'rt_lipLwr_rollOut',
                           'lipLwr_seal_out_cntr_left':'lf_lipLwr_rollOut_seal_cntr_diff',
                           'lipLwr_seal_out_cntr_right':'rt_lipLwr_rollOut_seal_cntr_diff',
                           'lipLwr_seal_out_outr_left':'lf_lipLwr_rollOut_seal_outr_diff',
                           'lipLwr_seal_out_outr_right':'rt_lipLwr_rollOut_seal_outr_diff',
                           'lipUpr_moreIn_left':'lf_lipUpr_moreIn',
                           'lipUpr_moreIn_right':'rt_lipUpr_moreIn',
                           'lipUpr_moreOut_left':'lf_lipUpr_moreOut',
                           'lipUpr_moreOut_right':'rt_lipUpr_moreOut',
                           'lipUpr_rollIn_left':'lf_lipUpr_rollIn',
                           'lipUpr_rollIn_right':'rt_lipUpr_rollIn',
                           'lipUpr_rollOut_left':'lf_lipUpr_rollOut',
                           'lipUpr_rollOut_right':'rt_lipUpr_rollOut',
                           'lipUpr_seal_out_cntr_left':'lf_lipUpr_rollOut_seal_cntr_diff',
                           'lipUpr_seal_out_cntr_right':'rt_lipUpr_rollOut_seal_cntr_diff',
                           'lipUpr_seal_out_outr_left':'lf_lipUpr_rollOut_seal_outr_diff',
                           'lipUpr_seal_out_outr_right':'rt_lipUpr_rollOut_seal_outr_diff',
                           'lipUpr_up_left':'lf_lipUpr_up',
                           'lipUpr_up_right':'rt_lipUpr_up',
                           'lipUpr_upSeal_cntr_left':'lf_lipUpr_upSeal_cntr',
                           'lipUpr_upSeal_cntr_right':'rt_lipUpr_upSeal_cntr',
                           'lipUpr_upSeal_outr_left':'lf_lipUpr_upSeal_outr',
                           'lipUpr_upSeal_outr_right':'rt_lipUpr_upSeal_outr',                           
                
                           }



"""
jawBase_rx
jawBase_ry
jawBase_rz
jawBase_tx
jawBase_ty
jawBase_tz
jawDriven_back_tz
jawDriven_dn_rx
jawDriven_dn_tz
jawDriven_fwd_tz
jawDriven_left_ry
jawDriven_left_rz
jawDriven_left_tx
jawDriven_right_ry
jawDriven_right_rz
jawDriven_right_tx
jawNDV_rx
jawNDV_ry
jawNDV_rz
jawNDV_tx
jawNDV_ty
jawNDV_tz



"""