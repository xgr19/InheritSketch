// table a cnt
Register<
bit<TABLEA_CNT_WIDTH>,
bit<TALBEA_SIZE_WIDTH> >(TABLEA_SIZE)  a_register_cnt;

RegisterAction<
bit<TABLEA_CNT_WIDTH>, 
bit<TALBEA_SIZE_WIDTH>, 
bit<TABLEA_CNT_WIDTH> >(a_register_cnt) a_read_cnt = {
	void apply(inout bit<TABLEA_CNT_WIDTH> register_data, out bit<TABLEA_CNT_WIDTH> cnt) {
		register_data = register_data + 1;
        if (register_data >= meta.min_count && register_data >= THRESHOLD_NUMBER){
            // resubmit
            cnt = register_data;
        } else {cnt = 0;}
	}
};
action ac_a_read_cnt(){meta.resubmit_data.a_count = a_read_cnt.execute(meta.idx_a);}

RegisterAction<
bit<TABLEA_CNT_WIDTH>, 
bit<TALBEA_SIZE_WIDTH>, 
bit<TABLEA_CNT_WIDTH> >(a_register_cnt) a_swap_cnt = {
	void apply(inout bit<TABLEA_CNT_WIDTH> register_data, out bit<TABLEA_CNT_WIDTH> cnt) {
		if(meta.min_count > register_data){
            register_data = meta.min_count;}
		cnt = register_data;
	}
};
action ac_a_swap_cnt(){
    a_swap_cnt.execute(meta.idx_a);
    return;
}
