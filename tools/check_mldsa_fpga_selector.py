#!/usr/bin/env python3
"""Compare the original/corrected security-level mux over every input basis bit."""
import argparse,json,subprocess,shutil
from pathlib import Path
from export_mldsa_fpga_latch_corrected import correct_selector,sha


def block(text):
    a=text.index('    always @(*) begin')
    b=text.index('    always @(*) begin',a+1)
    return text[a:b]


def run(original, corrected, out):
    original=Path(original).resolve();corrected=Path(corrected).resolve();out=Path(out).resolve()
    out.mkdir(parents=True,exist_ok=False)
    if correct_selector(original.read_text())!=corrected.read_text():
        raise ValueError('correction exceeds the two unsupported-selector defaults')
    for name,path in [('reference',original),('corrected',corrected)]:
        text='module '+name+'''(input [2:0] sec_lvl, input [511:0] C_SIPO,
        output reg [10:0] W1_LEN, output reg [9:0] C_SIPO_START,
        output reg [7:0] TAU, output reg [31:0] ctilde_out_len,
        output reg [63:0] ch);\n'''+block(path.read_text())+'endmodule\n'
        (out/(name+'.v')).write_text(text)
    tb='''module tb;
reg [2:0] sec_lvl; reg [511:0] C_SIPO;
wire [124:0] a,b;
reference r(sec_lvl,C_SIPO,a[124:114],a[113:104],a[103:96],a[95:64],a[63:0]);
corrected c(sec_lvl,C_SIPO,b[124:114],b[113:104],b[103:96],b[95:64],b[63:0]);
integer level,i,n; initial begin n=0;
for(level=0;level<8;level=level+1) begin
 if(level==2 || level==3 || level==5) begin
  sec_lvl=level;
  for(i=0;i<514;i=i+1) begin
   if(i<512) C_SIPO=512'b1<<i;
   else if(i==512) C_SIPO=0; else C_SIPO={512{1'b1}};
   #1; if(a!==b) $fatal(1,"supported selector mismatch"); n=n+1;
  end
 end
end
for(level=0;level<8;level=level+1) begin
 sec_lvl=level; C_SIPO={512{1'b1}}; #1;
 if(level!=2 && level!=3 && level!=5 && b!==0) $fatal(1,"unsupported selector not zero");
end
sec_lvl=3'bxxx; #1; if(b!==0) $fatal(1,"unknown selector not zero");
sec_lvl=3'bzzz; #1; if(b!==0) $fatal(1,"high impedance selector not zero");
$display("SELECTOR_PASS supported_basis_cases=%0d",n); $finish;
end endmodule
'''
    (out/'tb.v').write_text(tb)
    result={'status':'FAIL','source_hashes':{'original':sha(original),'corrected':sha(corrected)},'commands':[]}
    for cmd,log in [(['iverilog','-g2005','-s','tb','-o','tb.vvp','reference.v','corrected.v','tb.v'],'compile.log'),(['vvp','tb.vvp'],'simulate.log')]:
        result['commands'].append(cmd)
        p=subprocess.run(cmd,cwd=out,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=True)
        (out/log).write_text(p.stdout)
    if 'SELECTOR_PASS supported_basis_cases=1542' not in (out/'simulate.log').read_text():raise ValueError('missing completion')
    # Generic process lowering of the exact extracted selector, with no case assumptions.
    for name,expected in [('reference',3),('corrected',0)]:
        cmd=['yosys','-p',f'read_verilog {name}.v; hierarchy -top {name}; proc; write_json {name}.json']
        result['commands'].append(cmd)
        p=subprocess.run(cmd,cwd=out,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=True)
        (out/(name+'-yosys.log')).write_text(p.stdout)
        cells=json.loads((out/(name+'.json')).read_text())['modules'][name]['cells']
        latches=[v for v in cells.values() if 'latch' in v['type'].lower()]
        if len(latches)!=expected:raise ValueError('unexpected selector latch count')
        result[name+'_generic_latch_cells']=len(latches)
        result[name+'_generic_latch_bits']=sum(len(c['connections']['Q']) for c in latches)
    result.update(status='PASS',supported_selector_differential='PASS',supported_basis_cases=1542,
                  limits=['Extracted combinational selector only; full-core KAT and target Vivado checks reported separately.',
                          'The original generic latches total 64+10 bits before constant-bit optimization; Vivado reports 64+2 live bits.',
                          'Unsupported security levels remain unsupported even though these selector outputs are now zero.'])
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--original',required=True);p.add_argument('--corrected',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();print(json.dumps(run(a.original,a.corrected,a.out),indent=2))
