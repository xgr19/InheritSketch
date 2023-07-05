/*************************************************************************
*********************** Table p3 ***********************************
*************************************************************************/
// p3 ID
Register<
bit<FLOW_ID_WIDTH>,
bit<TALBEM_SIZE_WIDTH> >(TABLEM_SIZE)  p3_register_id;

// read ID
RegisterAction<
bit<FLOW_ID_WIDTH>, 
bit<TALBEM_SIZE_WIDTH>, 
bit<FLOW_ID_WIDTH> >(p3_register_id) p3_read_id = {
	void apply(inout bit<FLOW_ID_WIDTH> register_data, out bit<FLOW_ID_WIDTH> hit_) {
		if (register_data == meta.flowid) {
			hit_ = 1;
		} else {hit_ = 0;}
	}
};
action ac_p3_read_id(){meta.cls_flag3 = p3_read_id.execute(meta.idx_p3);}

// write ID
RegisterAction<
bit<FLOW_ID_WIDTH>, 
bit<TALBEM_SIZE_WIDTH>, 
bit<FLOW_ID_WIDTH> >(p3_register_id) p3_swap_id = {
	void apply(inout bit<FLOW_ID_WIDTH> register_data, out bit<FLOW_ID_WIDTH> flowid) {
		flowid = register_data;
		register_data = meta.flowid;
	}
};
action ac_p3_swap_id(){meta.flowid = p3_swap_id.execute(meta.idx_p3);}

// p3 CNT
Register<
bit<TABLEM_CNT_WIDTH>,
bit<TALBEM_SIZE_WIDTH> >(TABLEM_SIZE)  p3_register_cnt;

RegisterAction<
bit<TABLEM_CNT_WIDTH>, 
bit<TALBEM_SIZE_WIDTH>, 
bit<TABLEM_CNT_WIDTH> >(p3_register_cnt) p3_read_cnt = {
	void apply(inout bit<TABLEM_CNT_WIDTH> register_data, out bit<TABLEM_CNT_WIDTH> cnt) {
        cnt = register_data;
	}
};
action ac_p3_read_cnt(){meta.p3_count = p3_read_cnt.execute(meta.idx_p3);}


RegisterAction<
bit<TABLEM_CNT_WIDTH>, 
bit<TALBEM_SIZE_WIDTH>, 
bit<TABLEM_CNT_WIDTH> >(p3_register_cnt) p3_add_cnt = {
	void apply(inout bit<TABLEM_CNT_WIDTH> register_data, out bit<TABLEM_CNT_WIDTH> cnt) {
		cnt = register_data;
        register_data = register_data + 1;
	}
};
action ac_p3_add_cnt(){
    p3_add_cnt.execute(meta.idx_p3);
    return;
}

RegisterAction<
bit<TABLEM_CNT_WIDTH>, 
bit<TALBEM_SIZE_WIDTH>, 
bit<TABLEM_CNT_WIDTH> >(p3_register_cnt) p3_swap_cnt = {
	void apply(inout bit<TABLEM_CNT_WIDTH> register_data, out bit<TABLEM_CNT_WIDTH> cnt) {
		cnt = register_data;
        register_data = meta.resubmit_data.a_count;
	}
};
action ac_p3_swap_cnt(){
    meta.min_count = p3_swap_cnt.execute(meta.idx_p3);
}

// visit p3
@pragma stage 4
table visit_p3_id{
    actions = {ac_p3_read_id;}
    default_action = ac_p3_read_id;
}

@pragma stage 5
table visit_p3_cnt{
    key = {meta.cls_flag3: exact;}
    actions = {ac_p3_add_cnt; ac_p3_read_cnt;}
     // Cannot specify ac_p3_read_cnt as the default action, as it requires the hash distribution unit.
    // default_action = ac_p3_read_cnt();
    const entries = {
        (0): ac_p3_read_cnt();
        (1): ac_p3_add_cnt();
    }
}
