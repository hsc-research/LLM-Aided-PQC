"""Gate plumbing tests. Synthetic logs/mock AHB are NOT cryptographic RTL KATs."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("mlkem_adams_gate", ROOT / "tools/run_mlkem_adams_bridge_kat.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class AcvpMappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vectors = gate.load_vectors(gate.VENDOR / "test_vectors/nist_acvp_mlkem1024.json")
        cls.program, cls.cases = gate.build_commands(cls.vectors)

    def transcript(self):
        return "\n".join(f"MLKEM_CASE_PASS id={c['id']} checks={c['checks']} cycles=10000" for c in self.cases) + "\nMLKEM_ACVP_PASS cases=80 checks=39840\n"

    def test_official_full_coverage(self):
        self.assertEqual(len(self.cases), 80)
        self.assertEqual(sum(c["checks"] for c in self.cases), 39840)
        self.assertEqual([c["tcId"] for c in self.cases if c["implicit_rejection"]], [96, 98, 101, 104, 105])
        self.assertEqual(sum(c["expected_key_error"] for c in self.cases), 10)

    def test_full_output_byte_counts(self):
        for case in self.cases:
            if case["operation"] == "keyGen":
                self.assertEqual(case["compared_output_bytes"], 4736)
            elif case["operation"] == "encapsulation":
                self.assertEqual(case["compared_output_bytes"], 1600)
            elif case["operation"] == "decapsulation":
                self.assertEqual(case["compared_output_bytes"], 32)

    def test_endianness(self):
        self.assertEqual(gate.words_le(bytes.fromhex("00010203808182ff")), [0x03020100, 0xff828180])
        first = self.vectors["cases"][0]
        word = int.from_bytes(bytes.fromhex(first["input"]["d"])[:4], "little")
        self.assertIn(f"00000001 00009018 {word:08x}\n", self.program)

    def test_partial_word_rejected(self):
        with self.assertRaises(ValueError):
            gate.words_le(b"123")

    def test_malformed_or_short_data_rejected(self):
        for value in ["zz", "00", "00 " * 32]:
            with self.assertRaises(ValueError):
                gate.byte_array(value, "k")

    def test_changed_fixture_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "vector.json"
            target.write_text(json.dumps(self.vectors) + " ")
            with self.assertRaisesRegex(ValueError, "SHA256"):
                gate.load_vectors(target)

    def test_clean_synthetic_transcript_accepted_by_parser_only(self):
        self.assertTrue(gate.check_transcript(self.transcript(), self.cases, 0)[0])

    def test_empty_result_fails_closed(self):
        self.assertFalse(gate.check_transcript("", self.cases, 0)[0])

    def test_summary_only_fails_closed(self):
        self.assertFalse(gate.check_transcript("MLKEM_ACVP_PASS cases=80 checks=39840\n", self.cases, 0)[0])

    def test_nonzero_exit_fails_closed(self):
        self.assertFalse(gate.check_transcript(self.transcript(), self.cases, 1)[0])

    def test_missing_case_fails_closed(self):
        self.assertFalse(gate.check_transcript("\n".join(self.transcript().splitlines()[1:]), self.cases, 0)[0])

    def test_duplicate_case_fails_closed(self):
        self.assertFalse(gate.check_transcript(self.transcript().splitlines()[0] + "\n" + self.transcript(), self.cases, 0)[0])

    def test_wrong_checks_fails_closed(self):
        self.assertFalse(gate.check_transcript(self.transcript().replace("checks=1185", "checks=1184", 1), self.cases, 0)[0])

    def test_failure_with_success_marker_fails_closed(self):
        for failure in ["MLKEM_FAIL", "FATAL", "%Error", "ERROR"]:
            self.assertFalse(gate.check_transcript(self.transcript() + failure, self.cases, 0)[0])

    def test_missing_or_duplicate_summary_fails_closed(self):
        text = self.transcript()
        self.assertFalse(gate.check_transcript(text + text.splitlines()[-1], self.cases, 0)[0])
        self.assertFalse(gate.check_transcript("\n".join(text.splitlines()[:-1]), self.cases, 0)[0])

    def test_zero_cycle_or_malformed_case_fails_closed(self):
        for replacement in ["cycles=0", "cycles=x", "cycles=1 extra"]:
            self.assertFalse(gate.check_transcript(self.transcript().replace("cycles=10000", replacement, 1), self.cases, 0)[0])

    def test_early_summary_fails_closed(self):
        lines = self.transcript().splitlines()
        self.assertFalse(gate.check_transcript("\n".join([lines[-1], *lines[:-1]]), self.cases, 0)[0])

    def test_program_has_exact_check_and_case_accounting(self):
        commands = [tuple(int(x, 16) for x in line.split()) for line in self.program.splitlines()]
        self.assertEqual(sum(op == 2 for op, _, _ in commands), 39840 - 80)
        self.assertEqual(sum(op == 5 for op, _, _ in commands), 80)
        self.assertEqual(sum(op == 6 for op, _, _ in commands), 80)
        self.assertEqual(commands[-1], (7, 80, 39840))
        self.assertEqual(sum(op == 4 and val == 4 for op, _, val in commands), 10)


class CandidateIsolationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.candidate = Path(self.temp.name) / "upstream"
        shutil.copytree(gate.VENDOR / "upstream", self.candidate)
        self.relative = "src/abr_top/rtl/abr_ctrl.sv"

    def tearDown(self):
        self.temp.cleanup()

    def edit(self, relative, transform):
        path = self.candidate / relative
        path.write_text(transform(path.read_text()))

    def test_unchanged_copy_has_full_hash_inventory(self):
        hashes, changes = gate.candidate_inputs(self.candidate)
        self.assertEqual(len(hashes), 221)
        self.assertEqual(changes, [])

    def test_permitted_rtl_fault_is_hashed_as_modified(self):
        self.edit(self.relative, lambda text: text.replace(
            "MLKEM_ENCAPS_KEY.rd_data = encapskey_rd_ack & mlkem_valid_reg ? privkey_out_rdata : '0;",
            "MLKEM_ENCAPS_KEY.rd_data = encapskey_rd_ack & mlkem_valid_reg ? (privkey_out_rdata ^ 32'h1) : '0;"))
        _, changes = gate.candidate_inputs(self.candidate)
        self.assertEqual([c["path"] for c in changes], [self.relative])
        self.assertNotEqual(changes[0]["reference_sha256"], changes[0]["candidate_sha256"])

    def test_reference_or_ancestor_cannot_be_candidate(self):
        for target in (gate.VENDOR / "upstream", gate.VENDOR):
            with self.assertRaisesRegex(ValueError, "separate directory"):
                gate.candidate_inputs(target)

    def test_extra_source_rejected(self):
        (self.candidate / "fake_tb.sv").write_text("module fake_tb; endmodule")
        with self.assertRaisesRegex(ValueError, "inventory"):
            gate.candidate_inputs(self.candidate)

    def test_missing_source_rejected(self):
        (self.candidate / self.relative).unlink()
        with self.assertRaisesRegex(ValueError, "inventory"):
            gate.candidate_inputs(self.candidate)

    def test_symlink_file_rejected(self):
        path = self.candidate / self.relative
        path.unlink()
        path.symlink_to(gate.VENDOR / "upstream" / self.relative)
        with self.assertRaisesRegex(ValueError, "symlinks"):
            gate.candidate_inputs(self.candidate)

    def test_changed_source_manifest_rejected(self):
        self.edit("SOURCE_MANIFEST.json", lambda text: text + "\n")
        with self.assertRaisesRegex(ValueError, "protected"):
            gate.candidate_inputs(self.candidate)

    def test_masking_configuration_is_protected(self):
        self.edit("src/abr_top/rtl/abr_config_defines.svh", lambda text: text + "\n")
        with self.assertRaisesRegex(ValueError, "protected"):
            gate.candidate_inputs(self.candidate)

    def test_assertion_headers_are_protected(self):
        self.edit("src/abr_prim/rtl/abr_prim_assert.sv", lambda text: text + "\n")
        with self.assertRaisesRegex(ValueError, "protected"):
            gate.candidate_inputs(self.candidate)

    def test_new_include_rejected(self):
        self.edit(self.relative, lambda text: text + '\n`include "/tmp/unreviewed.sv"\n')
        with self.assertRaisesRegex(ValueError, "include directives"):
            gate.candidate_inputs(self.candidate)

    def test_simulator_control_and_host_calls_rejected(self):
        original = (self.candidate / self.relative).read_text()
        for token in ("$finish", "$system", "$fopen", "$display"):
            (self.candidate / self.relative).write_text(original + "\n" + token + ";\n")
            with self.assertRaisesRegex(ValueError, "simulator calls"):
                gate.candidate_inputs(self.candidate)

    def test_filelist_keeps_harness_and_wrapper_original(self):
        manifest = json.loads((gate.VENDOR / "integration/manifest.json").read_text())
        text = gate.compile_filelist(gate.VENDOR, manifest, self.candidate)
        self.assertIn(str(self.candidate / self.relative), text)
        self.assertIn(str(gate.VENDOR / "integration/abr_unified_top.sv"), text)
        self.assertTrue(text.endswith(str(gate.TB) + "\n"))
        self.assertNotIn(str(self.candidate / "integration"), text)


@unittest.skipUnless(shutil.which("iverilog") and shutil.which("vvp"), "Icarus needed only for the non-cryptographic AHB plumbing test")
class AhbPlumbingTests(unittest.TestCase):
    # A mock register slave validates byte lanes and BFM timing, not ML-KEM.
    MOCK = r'''
`timescale 1ns/1ps
module abr_unified_top(input wire clk, rst_b, input wire [31:0] haddr_i,
 input wire [63:0] hwdata_i, input wire hsel_i, hwrite_i, hready_i,
 input wire [1:0] htrans_i, input wire [2:0] hsize_i,
 output wire hresp_o, hreadyout_o, output wire [63:0] hrdata_o,
 input wire debugUnlock_or_scan_mode_switch, output wire busy_o, error_intr, notif_intr);
 reg [31:0] address=0, lo=0, hi=0; reg pending=0, wr=0, complete=0;
 reg [31:0] data; integer waits=0, settle=0;
 assign hreadyout_o = !(pending && waits<2);
 assign hresp_o=0; assign busy_o=0; assign error_intr=0; assign notif_intr=0;
 assign hrdata_o = address[2] ? {data,32'b0} : {32'b0,data};
 always @* case(address)
 'h9014: data=complete ? 2 : 1;
 'h9018: data=lo;
 'h901c: data=hi;
 default: data=0;
 endcase
 always @(posedge clk) begin
  if (!rst_b) begin pending<=0; wr<=0; complete<=0; lo<=0; hi<=0; waits<=0; settle<=0; end
  else begin
   if(complete && settle<20) settle<=settle+1;
   if(pending && !hreadyout_o) waits<=waits+1;
   if(hready_i) begin
    if(pending && wr) begin
     case(address)
     'h9018: lo<=hwdata_i[31:0];
     'h901c: hi<=hwdata_i[63:32];
     'h9010: complete<=1;
     endcase
    end
    pending<=hsel_i && htrans_i[1];
    if(hsel_i && htrans_i[1]) begin address<=haddr_i; wr<=hwrite_i; waits<=0; end
   end
  end
 end
endmodule
'''
    PROGRAM = """00000005 00000000 00000001
00000003 00000000 00000000
00000001 00009018 03020100
00000001 0000901c ff828180
00000001 00009010 00000001
00000004 00009014 00000003
00000002 00009018 03020100
00000002 0000901c ff828180
00000006 00000001 00000003
00000007 00000001 00000003
"""
    def execute(self, program):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            mock, commands, binary = work / "mock.sv", work / "commands.hex", work / "tb.vvp"
            mock.write_text(self.MOCK)
            commands.write_text(program)
            compiled = subprocess.run(["iverilog", "-g2012", "-s", "tb_mlkem_acvp", "-o", str(binary), str(mock), str(gate.TB)], capture_output=True, text=True, timeout=30)
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            return subprocess.run(["vvp", str(binary), f"+COMMANDS={commands}", "+MAX_CYCLES=1000"], capture_output=True, text=True, timeout=30)

    def test_word_lanes_and_stalled_data_phases(self):
        result = self.execute(self.PROGRAM)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("MLKEM_ACVP_PASS cases=1 checks=3", result.stdout)

    def test_corrupt_expected_word_causes_real_fatal(self):
        result = self.execute(self.PROGRAM.replace("00000002 0000901c ff828180", "00000002 0000901c ff828181"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("reason=word_mismatch", result.stdout)
        self.assertNotIn("MLKEM_ACVP_PASS", result.stdout)

    def test_junk_after_terminator_causes_real_fatal(self):
        result = self.execute(self.PROGRAM + "this is not a command\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("reason=data_after_terminator", result.stdout)

    def test_missing_terminator_causes_real_fatal(self):
        result = self.execute("\n".join(self.PROGRAM.splitlines()[:-1]) + "\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("reason=missing_terminator", result.stdout)


@unittest.skipUnless(shutil.which("verilator"), "Verilator needed for clean-shutdown regression")
class VerilatorShutdownTests(unittest.TestCase):
    def test_mock_ahb_completion_has_clean_simulator_exit(self):
        # This is still a mock slave; only process/command-loop behavior is tested.
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            mock = work / "mock.sv"
            mock.write_text(AhbPlumbingTests.MOCK)
            commands = work / "commands.hex"
            commands.write_text(AhbPlumbingTests.PROGRAM)
            compiled = subprocess.run(["verilator", "--binary", "--timing", "-Wno-fatal",
                                       "--top-module", "tb_mlkem_acvp", "--Mdir", str(work / "obj_dir"),
                                       str(mock), str(gate.TB)], capture_output=True, text=True, timeout=120)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            result = subprocess.run([str(work / "obj_dir/Vtb_mlkem_acvp"),
                                     f"+COMMANDS={commands}", "+MAX_CYCLES=1000"],
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("MLKEM_ACVP_PASS cases=1 checks=3", result.stdout)


if __name__ == "__main__":
    unittest.main()
