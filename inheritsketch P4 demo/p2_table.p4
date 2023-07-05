/*************************************************************************
*********************** Table p2 ***********************************
*************************************************************************/
// p2 ID
Register<
bit<FLOW_ID_WIDTH>,
bit<TALBEM_SIZE_WIDTH> >(TABLEM_SIZE)  p2_register_id;

// read ID
RegisterAction<
bit<FLOW_ID_WIDTH>, 
bit<TALBEM_SIZE_WIDTH>, 
bit<FLOW_ID_WIDTH> >(p2_register_id) p2_read_id = {
	void apply(inout bit<FLOW_ID_WIDTH> register_data, out bit<FLOW_ID_WIDTH> hit_) {
		if (register_data == meta.flowid) {
			hit_ = 1;
		} else {hit_ = 0;}
	}
};
action ac_p2_read_id(){meta.cls_flag2 = p2_read_id.execute(meta.idx_p2);}

// write ID
RegisterAction<
bit<FLOW_ID_WIDTH>, 
bit<TALBEM_SIZE_WIDTH>, 
bit<FLOW_ID_WIDTH> >(p2_register_id) p2_swap_id = {
	void apply(inout bit<FLOW_ID_WIDTH> register_data, out bit<FLOW_ID_WIDTH> flowid) {
		flowid = register_data;
		register_data = meta.flowid;
	}
};
action ac_p2_swap_id(){meta.flowid = p2_swap_id.execute(meta.idx_p2);}

// p2 CNT
Register<
bit<TABLEM_CNT_WIDTH>,
bit<TALBEM_SIZE_WIDTH> >(TABLEM_SIZE)  p2_register_cnt;

RegisterAction<
bit<TABLEM_CNT_WIDTH>, 
bit<TALBEM_SIZE_WIDTH>, 
bit<TABLEM_CNT_WIDTH> >(p2_register_cnt) p2_read_cnt = {
	void apply(inout bit<TABLEM_CNT_WIDTH> register_data, out bit<TABLEM_CNT_WIDTH> cnt) {
        cnt = register_data;
	}
};
action ac_p2_read_cnt(){meta.p2_count = p2_read_cnt.execute(meta.idx_p2);}


RegisterAction<
bit<TABLEM_CNT_WIDTH>, 
bit<TALBEM_SIZE_WIDTH>, 
bit<TABLEM_CNT_WIDTH> >(p2_register_cnt) p2_add_cnt = {
	void apply(inout bit<TABLEM_CNT_WIDTH> register_data, out bit<TABLEM_CNT_WIDTH> cnt) {
		cnt = register_data;
        register_data = register_data + 1;
	}
};
action ac_p2_add_cnt(){
    p2_add_cnt.execute(meta.idx_p2);
    return;
}

RegisterAction<
bit<TABLEM_CNT_WIDTH>, 
bit<TALBEM_SIZE_WIDTH>, 
bit<TABLEM_CNT_WIDTH> >(p2_register_cnt) p2_swap_cnt = {
	void apply(inout bit<TABLEM_CNT_WIDTH> register_data, out bit<TABLEM_CNT_WIDTH> cnt) {
		cnt = register_data;
        register_data = meta.resubmit_data.a_count;
	}
};
action ac_p2_swap_cnt(){
    meta.min_count = p2_swap_cnt.execute(meta.idx_p2);
}

// visit p2
@pragma stage 3
table visit_p2_id{
    actions = {ac_p2_read_id;}
    default_action = ac_p2_read_id;
}

@pragma stage 4
table visit_p2_cnt{
    key = {meta.cls_flag2: exact;}
    actions = {ac_p2_add_cnt; ac_p2_read_cnt;}
     // Cannot specify ac_p2_read_cnt as the default action, as it requires the hash distribution unit.
    // default_action = ac_p2_read_cnt();
    const entries = {
        (0): ac_p2_read_cnt();
        (1): ac_p2_add_cnt();
    }
}
