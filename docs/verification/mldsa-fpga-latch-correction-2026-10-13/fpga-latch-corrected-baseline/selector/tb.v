module tb;
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
