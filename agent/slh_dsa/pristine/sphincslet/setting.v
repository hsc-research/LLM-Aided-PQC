//-- SHAKE256 version or SHA-2 version --//
//-- When define SHAKE, it works as SHAKE256 version --//
//-- When undefine SHAKE, it works as SHA-2 version --//
//`define SHAKE

//-- Select target parameter --//
//`define PARAM_128S
`define PARAM_128F
//`define PARAM_192S
//`define PARAM_192F
//`define PARAM_256S
//`define PARAM_256F


`ifdef PARAM_128F
    `define PARAM_128
    `define PARAM_SET "128f"
`endif
`ifdef PARAM_128S
    `define PARAM_128
    `define PARAM_SET "128s"
`endif

`ifdef PARAM_192F
    `define PARAM_192
    `define PARAM_SET "192f"
`endif
`ifdef PARAM_192S
    `define PARAM_192
    `define PARAM_SET "192s"
`endif

`ifdef PARAM_256F
    `define PARAM_256
    `define PARAM_SET "256f"
`endif
`ifdef PARAM_256S
    `define PARAM_256
    `define PARAM_SET "256s"
`endif

`ifdef SHAKE
    `define HASH1 "SHAKE"
`else
    `define SHA2
    `ifdef PARAM_128
        `define HASH1 "SHA256"
    `else
        `define HASH1 "SHA256"
        `define HASH2 "SHA512"    
    `endif
`endif
