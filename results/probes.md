| Probe | | Note |
|---|---|---|
| python | ✅ | 3.12.15 (Windows-11-10.0.26200-SP0) |
| disk | ✅ | 43.9 GB free of 98.8 GB on D:\ |
| ram | ✅ | 6.2 GB available of 16.9 GB |
| torch | ✅ | 2.14.1+cpu, cuda=False |
| tinker Qwen/Qwen3.5-4B | ✅ | LoRA r16 client ok; tokenizer=Qwen/Qwen3.5-4B (tinker 0.33.1) |
| tinker Qwen/Qwen3-8B | ✅ | LoRA r16 client ok; tokenizer=Qwen/Qwen3-8B (tinker 0.33.1) |
| tabpfn | ✗ | licence accepted, token read; weight download tabpfn-v3.5-20260909.safetensors stalled at 804 MB (run 1) and 0 B (run 2); process killed manually, no fit |
| open-meteo | ✅ | not reached in this run (process killed during TabPFN); previous run: 24 hourly rows, pressure_msl 1007.4-1013.3 hPa, cloud_cover 0-11% |

Run 2026-10-10 ~22:04 PKT. Table written by hand from console output because the run was killed before `probes.py` could write it.
