import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gpu_nvml_exporter as ex  # noqa: E402


class PureHelpersTest(unittest.TestCase):
    def test_cgroup_v2_and_v1(self):
        cid = "59038e41130087f8a9d7e957c81e17cf88018a6440acfc30f3a898ad95229bce"
        self.assertEqual(ex.container_id_from_cgroup(f"0::/system.slice/docker-{cid}.scope\n"), cid)
        self.assertEqual(ex.container_id_from_cgroup(f"12:memory:/docker/{cid}\n"), cid)
        self.assertIsNone(ex.container_id_from_cgroup("0::/user.slice/user-1000.slice/session-3.scope\n"))

    def test_xid_line_and_pci_mapping(self):
        line = "NVRM: Xid (PCI:0000:01:00): 79, pid=1234, name=llama-server, GPU has fallen off the bus."
        bus, code = ex.parse_xid_line(line)
        self.assertEqual(code, 79)
        self.assertEqual(ex.pci_key(bus), ex.pci_key("00000000:01:00.0"))
        self.assertNotEqual(ex.pci_key("00000000:02:00.0"), ex.pci_key(bus))
        self.assertIsNone(ex.parse_xid_line("NVRM: loading NVIDIA UNIX Open Kernel Module for x86_64  580.00"))

    def test_gpm_units(self):
        self.assertAlmostEqual(ex.scale_gpm(87.5, "%"), 0.875)
        self.assertEqual(ex.scale_gpm(1.5, "MiB/s"), 1.5 * 1048576)
        self.assertIsNone(ex.scale_gpm(1.0, "furlongs"))

    def test_mem_bandwidth_constant_resolves(self):
        names = dict(ex.GPM_RATIOS)["mem_bandwidth_util"]
        self.assertTrue(any(hasattr(ex.N, "NVML_GPM_METRIC_" + n) for n in names))


if __name__ == "__main__":
    unittest.main()
