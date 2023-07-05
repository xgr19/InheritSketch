/*************************************************************************
*********************** Table p1 ***********************************
*************************************************************************/
// p1 ID
Register<
bit<FLOW_ID_WIDTH>,
bit<TALBEM_SIZE_WIDTH> >(TABLEM_SIZE)  p1_register_id;

// read ID
RegisterAction<
bit<FLOW_ID_WIDTH>, 
bit<TALBEM_SIZE_WIDTH>, 
bit<FLOW_ID_WIDTH> >(p1_register_id) p1_read_id = {
	void apply(inout bit<FLOW_ID_WIDTH> register_data, out bit<FLOW_ID_WIDTH> hit_) {
		if (register_data == meta.flowid) {
			hit_ = 1;
		} else {hit_ = 0;}
	}
};
action ac_p1_read_id(){meta.cls_flag1 = p1_read_id.execute(meta.idx_p1);}

// write ID
RegisterAction<
bit<FLOW_ID_WIDTH>, 
bit<TALBEM_SIZE_WIDTH>, 
bit<FLOW_ID_WIDTH> >(p1_register_id) p1_swap_id = {
	void apply(inout bit<FLOW_ID_WIDTH> register_data, out bit<FLOW_ID_WIDTH> flowid) {
		flowid = register_data;
		register_data = meta.flowid;
	}
};
action ac_p1_swap_id(){meta.flowid = p1_swap_id.execute(meta.idx_p1);}

// p1 CNT
Register<
bit<TABLEM_CNT_WIDTH>,
bit<TALBEM_SIZE_WIDTH> >(TABLEM_SIZE)  p1_register_cnt;

RegisterAction<
bit<TABLEM_CNT_WIDTH>, 
bit<TALBEM_SIZE_WIDTH>, 
bit<TABLEM_CNT_WIDTH> >(p1_register_cnt) p1_read_cnt = {
	void apply(inout bit<TABLEM_CNT_WIDTH> register_data, out bit<TABLEM_CNT_WIDTH> cnt) {
        cnt = register_data;
	}
};
action ac_p1_read_cnt(){meta.p1_count = p1_read_cnt.execute(meta.idx_p1);}


RegisterAction<
bit<TABLEM_CNT_WIDTH>, 
bit<TALBEM_SIZE_WIDTH>, 
bit<TABLEM_CNT_WIDTH> >(p1_register_cnt) p1_add_cnt = {
	void apply(inout bit<TABLEM_CNT_WIDTH> register_data, out bit<TABLEM_CNT_WIDTH> cnt) {
		cnt = register_data;
        register_data = register_data + 1;
	}
};
action ac_p1_add_cnt(){
    p1_add_cnt.execute(meta.idx_p1);
}

RegisterAction<
bit<TABLEM_CNT_WIDTH>, 
bit<TALBEM_SIZE_WIDTH>, 
bit<TABLEM_CNT_WIDTH> >(p1_register_cnt) p1_swap_cnt = {
	void apply(inout bit<TABLEM_CNT_WIDTH> register_data, out bit<TABLEM_CNT_WIDTH> cnt) {
		cnt = register_data;
        register_data = meta.resubmit_data.a_count;
	}
};
action ac_p1_swap_cnt(){
    meta.min_count = p1_swap_cnt.execute(meta.idx_p1);
}

// visit p1
@pragma stage 2
table visit_p1_id{
    actions = {ac_p1_read_id;}
    default_action = ac_p1_read_id;
}

@pragma stage 3
table visit_p1_cnt{
    key = {meta.cls_flag1: exact;}
    actions = {ac_p1_add_cnt; ac_p1_read_cnt;}
     // Cannot specify ac_p1_read_cnt as the default action, as it requires the hash distribution unit.
    // default_action = ac_p1_read_cnt();
    const entries = {
        (0): ac_p1_read_cnt();
        (1): ac_p1_add_cnt();
    }
}
