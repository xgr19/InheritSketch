 /* -*- P4_16 -*- */

/*
 * Copyright (c) pcl, Inc.
 *
 *
 *Author：pcl:lll, xgr
 */

#include <core.p4>
#include <tna.p4>

#define FLOW_ID_WIDTH 32
//** 2^10 = 1024 per primary table, 3 p tables, cnter with 32 bits
#define TALBEM_SIZE_WIDTH 10
#define TABLEM_SIZE 1024
#define TABLEM_CNT_WIDTH  32

//** 1 assistant table， 2^17 = 131072
#define TALBEA_SIZE_WIDTH 17
#define TABLEA_SIZE 131072
#define TABLEA_CNT_WIDTH  32
// if 附表cnt > max(min_counter.cnt, 100): resubmit
#define THRESHOLD_NUMBER 50

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/
header ethernet_t {
    bit<48>    dstAddr;
    bit<48>    srcAddr;
    bit<16>    etherType;
}

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    bit<32>   srcAddr;
    bit<32>   dstAddr;
}

// resubmit data
header resubmit_h {
    // total should be 64 bits, pad 24bits together is forbid...
    bit<TABLEA_CNT_WIDTH>      a_count;
    bit<8>                     init_num;  // replace which p table
    bit<8>                     pad0;
    bit<8>                     pad1;
    bit<8>                     pad2;
}

struct my_ingress_metadata_t {
    resubmit_h  resubmit_data;

    // 主表 primary table
    bit<TALBEM_SIZE_WIDTH>  idx_p1;
    bit<TALBEM_SIZE_WIDTH>  idx_p2;
    bit<TALBEM_SIZE_WIDTH>  idx_p3;
    // 附表 assistant table
    bit<TALBEA_SIZE_WIDTH>  idx_a;

    // hash src+dst ip to flowid
    bit<FLOW_ID_WIDTH>      flowid;
    bit<FLOW_ID_WIDTH>      tmp_flowid;

    // register return id
    bit<FLOW_ID_WIDTH>      p1_flowid;
    bit<FLOW_ID_WIDTH>      p2_flowid;
    bit<FLOW_ID_WIDTH>      p3_flowid;

    bit<TABLEM_CNT_WIDTH>   p1_count;
    bit<TABLEM_CNT_WIDTH>   p2_count;
    bit<TABLEM_CNT_WIDTH>   p3_count;


    bit<TABLEM_CNT_WIDTH>   cal_1_2;
    bit<TABLEM_CNT_WIDTH>   cal_2_3;
    bit<TABLEM_CNT_WIDTH>   cal_3_1;

    //min cnt in primary, or the swap cnt
    bit<TABLEM_CNT_WIDTH>   min_count;

    bit<FLOW_ID_WIDTH>  	cls_flag1; // hit p1 or not
    bit<FLOW_ID_WIDTH>  	cls_flag2; // hit p2 or not
    bit<FLOW_ID_WIDTH>  	cls_flag3; // hit p3 or not

    bit<FLOW_ID_WIDTH>  	cls_flag; // heavy or not

    bit<8>                  port_index;
}

struct my_ingress_headers_t {
    ethernet_t  ethernet;
    ipv4_t      ipv4;
}


const bit<16> TYPE_IPV4 = 0x800;

/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/
parser IngressParser(packet_in        pkt,
    out my_ingress_headers_t          hdr,
    out my_ingress_metadata_t         meta,
    out ingress_intrinsic_metadata_t  ig_intr_md)
{
    state start {
		pkt.extract(ig_intr_md);
		transition select(ig_intr_md.resubmit_flag){
            1: parse_resubmit;
            0: parse_port_metadata;
        }
    }
	
    state parse_resubmit {
        pkt.extract(meta.resubmit_data);
        transition parse_ethernet;
    }

	state parse_port_metadata {
	   pkt.advance(PORT_METADATA_SIZE);
	   transition parse_ethernet;
	}

    state parse_ethernet {
        pkt.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_IPV4   : parse_ipv4;
        }
    }
   
   state parse_ipv4 {
        pkt.extract(hdr.ipv4);
        meta.cls_flag = 0;  // not heavy initially
        transition accept;
   }

}

control Psketch(
    /* User */
    inout my_ingress_headers_t                       hdr,
    inout my_ingress_metadata_t                      meta,
    /* Intrinsic */
    in    ingress_intrinsic_metadata_t               ig_intr_md,
    in    ingress_intrinsic_metadata_from_parser_t   ig_prsr_md,
    inout ingress_intrinsic_metadata_for_deparser_t  ig_dprsr_md,
    inout ingress_intrinsic_metadata_for_tm_t        ig_tm_md)
{
    #include "p1_table.p4"
    #include "p2_table.p4"
    #include "p3_table.p4"
    #include "a_table.p4"

    Hash< bit<FLOW_ID_WIDTH> >(HashAlgorithm_t.CRC32) hash_flowid;
    action cal_hash_flowid(){
    	meta.flowid = hash_flowid.get({hdr.ipv4.srcAddr, hdr.ipv4.dstAddr}); 
        meta.tmp_flowid = hash_flowid.get({hdr.ipv4.srcAddr, hdr.ipv4.dstAddr});
    }
    
    // ** 哈希函数种子要不一样??
    CRCPolynomial<bit<32>>( coeff    = 0x04C11DB7,
                            reversed = true,
                            msb      = false,
                            extended = false,
                            init     = 0xFFFFFFFF,
                            xor      = 0xFFFFFFFF) poly1;
    Hash<bit<TALBEM_SIZE_WIDTH>>(HashAlgorithm_t.CUSTOM, poly1) hash_p1;
    // a table can only process 32 bit hash, so we separate to several tables...
    action ac_hash_p1(){meta.idx_p1 = hash_p1.get({meta.flowid});}
    table cal_hash_p1{
        actions = {ac_hash_p1;}
        default_action = ac_hash_p1();
    }

    CRCPolynomial<bit<32>>( coeff    = 0x1EDC6F41,
                            reversed = true,
                            msb      = false,
                            extended = false,
                            init     = 0xFFFFFFFF,
                            xor      = 0xFFFFFFFF) poly2;
    Hash<bit<TALBEM_SIZE_WIDTH>>(HashAlgorithm_t.CUSTOM, poly2) hash_p2;
    action ac_hash_p2(){meta.idx_p2 = hash_p2.get({meta.flowid});}
    table cal_hash_p2{
        actions = {ac_hash_p2;}
        default_action = ac_hash_p2();
    }

    CRCPolynomial<bit<32>>( coeff    = 0xA833982B,
                            reversed = true,
                            msb      = false,
                            extended = false,
                            init     = 0xFFFFFFFF,
                            xor      = 0xFFFFFFFF) poly3;
    Hash<bit<TALBEM_SIZE_WIDTH>>(HashAlgorithm_t.CUSTOM, poly3) hash_p3;
    action ac_hash_p3(){meta.idx_p3 = hash_p3.get({meta.flowid});}
    table cal_hash_p3{
        actions = {ac_hash_p3;}
        default_action = ac_hash_p3();
    }

	Hash<bit<TALBEA_SIZE_WIDTH>>(HashAlgorithm_t.CRC32) hash_a;

    action forward(){ig_tm_md.ucast_egress_port=1;}

    // find the min cnt in p tables
    action min_p1(){
        meta.resubmit_data.init_num = 1;
        meta.min_count = meta.p1_count;
    }
    action min_p2(){
        meta.resubmit_data.init_num = 2;
        meta.min_count = meta.p2_count;
    }
    action min_p3(){
        meta.resubmit_data.init_num = 3;
        meta.min_count = meta.p3_count;
    }
    table find_min_p{
        key = {
            meta.cal_1_2:ternary;
            meta.cal_2_3:ternary;
            meta.cal_3_1:ternary;
        }
        actions = {min_p1; min_p2; min_p3;}
        // It is weird, this const entries cause segmentation fault, 
        // we decide to install them via bfshell(controller)...
        const entries = {
            (0&&&0x80000000, 0&&&0x80000000, 0&&&0x80000000): min_p1();
            (1&&&0x80000000, 0&&&0x80000000, 0&&&0x80000000): min_p1();
            (1&&&0x80000000, 1&&&0x80000000, 0&&&0x80000000): min_p1();

            (0&&&0x80000000, 1&&&0x80000000, 0&&&0x80000000): min_p2();
            (0&&&0x80000000, 1&&&0x80000000, 1&&&0x80000000): min_p2();

            (0&&&0x80000000, 0&&&0x80000000, 1&&&0x80000000): min_p3();
            (1&&&0x80000000, 0&&&0x80000000, 1&&&0x80000000): min_p3();
        }
    }

    apply{
        // stage 0
        forward();
		cal_hash_flowid();
        // stage 1
		cal_hash_p1.apply();
        cal_hash_p2.apply();
        cal_hash_p3.apply();
        meta.idx_a = hash_a.get({meta.flowid});

        if (ig_intr_md.resubmit_flag == 0) {
            // stage 2
            visit_p1_id.apply();
            // stage 3
            visit_p1_cnt.apply();
            visit_p2_id.apply();
            // stage 4
            visit_p2_cnt.apply();
            visit_p3_id.apply();
            // stage 5
            visit_p3_cnt.apply();
            // stage 6, if hit the primary table: cls_flag1/2/3 = 1
    	    if(meta.cls_flag1 == 1||meta.cls_flag2 == 1||meta.cls_flag3 == 1){
        		meta.cls_flag = 1;
        		return; // stop the current control statement
    	    }
            meta.cal_1_2 = meta.p1_count - meta.p2_count;
            meta.cal_2_3 = meta.p2_count - meta.p3_count;
            meta.cal_3_1 = meta.p3_count - meta.p1_count;
            // stage 7
            find_min_p.apply();
            // stage 8
            ac_a_read_cnt();
            // stage 9
            if (meta.resubmit_data.a_count != 0) {
                ig_dprsr_md.resubmit_type = 2; } // resubmit
        } else {
            if (meta.resubmit_data.init_num == 1){
                ac_p1_swap_id();
                ac_p1_swap_cnt();
            }
            if (meta.resubmit_data.init_num == 2){
                ac_p2_swap_id();
                ac_p2_swap_cnt();
            }
            if (meta.resubmit_data.init_num == 3){
                ac_p3_swap_id();
                ac_p3_swap_cnt();
            }
            if(meta.resubmit_data.init_num != 0){
                meta.idx_a = hash_a.get({meta.flowid});
                ac_a_swap_cnt();
            }


        }
        // ig_tm_md.bypass_egress = 1w1;

    }

}



control Ingress(
    /* User */
    inout my_ingress_headers_t                       hdr,
    inout my_ingress_metadata_t                      meta,
    /* Intrinsic */
    in    ingress_intrinsic_metadata_t               ig_intr_md,
    in    ingress_intrinsic_metadata_from_parser_t   ig_prsr_md,
    inout ingress_intrinsic_metadata_for_deparser_t  ig_dprsr_md,
    inout ingress_intrinsic_metadata_for_tm_t        ig_tm_md)
 {
    Psketch() psketch;
    apply{
        psketch.apply(hdr, meta, ig_intr_md, ig_prsr_md, ig_dprsr_md, ig_tm_md);
    }
 }



control IngressDeparser(packet_out pkt,
    /* User */
    inout my_ingress_headers_t                       hdr,
    in    my_ingress_metadata_t                      meta,
    /* Intrinsic */
    in    ingress_intrinsic_metadata_for_deparser_t  ig_dprsr_md)
{
    Resubmit() resubmit;
    apply {
        // resubmit with resubmit_data
       if (ig_dprsr_md.resubmit_type == 2) {
           resubmit.emit(meta.resubmit_data);
       }
       pkt.emit(hdr);
    }
}



/*************************************************************************
 ****************  E G R E S S   P R O C E S S I N G   *******************
 *************************************************************************/

    /***********************  H E A D E R S  ************************/

struct my_egress_headers_t {
}

    /********  G L O B A L   E G R E S S   M E T A D A T A  *********/

struct my_egress_metadata_t {
}

    /***********************  P A R S E R  **************************/

parser EgressParser(packet_in        pkt,
    /* User */
    out my_egress_headers_t          hdr,
    out my_egress_metadata_t         meta,
    /* Intrinsic */
    out egress_intrinsic_metadata_t  eg_intr_md)
{
    /* This is a mandatory state, required by Tofino Architecture */
    state start {
        pkt.extract(eg_intr_md);
        transition accept;
    }
}

    /***************** M A T C H - A C T I O N  *********************/

control Egress(
    /* User */
    inout my_egress_headers_t                          hdr,
    inout my_egress_metadata_t                         meta,
    /* Intrinsic */    
    in    egress_intrinsic_metadata_t                  eg_intr_md,
    in    egress_intrinsic_metadata_from_parser_t      eg_prsr_md,
    inout egress_intrinsic_metadata_for_deparser_t     eg_dprsr_md,
    inout egress_intrinsic_metadata_for_output_port_t  eg_oport_md)
{
    apply {
    }
}

    /*********************  D E P A R S E R  ************************/

control EgressDeparser(packet_out pkt,
    /* User */
    inout my_egress_headers_t                       hdr,
    in    my_egress_metadata_t                      meta,
    /* Intrinsic */
    in    egress_intrinsic_metadata_for_deparser_t  eg_dprsr_md)
{
    apply {
        pkt.emit(hdr);
    }
}


/************ F I N A L   P A C K A G E ******************************/
Pipeline(
    IngressParser(),
    Ingress(),
    IngressDeparser(),
    EgressParser(),
    Egress(),
    EgressDeparser()
) pipe;

Switch(pipe) main;
