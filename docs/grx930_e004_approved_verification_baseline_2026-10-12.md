# GRX930 Engineering-Verification Baseline Review

**Review date:** 2026-10-12
**Approval:** **Approved by Kubeworkz for GRX930 engineering verification only.**
**Approval scope:** The exact source inputs, firmware, and harness variants enumerated below. This is not approval of results, product scope, E-002/E-004 closure, four-core correctness, FPGA/ASIC readiness, manufacturing, tapeout, supplier commitments, or spending.

This review identifies the input snapshots used by the recorded E-004 simulation runs. It does not identify upstream provenance: the source copy has no nested Git metadata. The reference repository was `C:/Users/kubew/grx930`, branch `npu/shim-tile-model`, HEAD `907fcb7e387e5fc0b3f7c4676b22ff9d37301afb`. The checked-out repository had local uncommitted/untracked files at review time. The approval applies to these enumerated E-004 inputs, not to the whole mutable checkout or a broad directory snapshot.

## Recorded source invocations

Both saved Verilator metadata files record 65 compiler source inputs: 38 CPU files, 25 C930 RTL files, and two harness files. Because the two runs use different harness pairs, their union contains 67 unique source paths. The hashes below are SHA-256 of each imported source file as present in the review workspace.

Input-list fingerprints (SHA-256 over sorted `file_sha256  invocation_path\n` records):

- Four-core suite: `9ea142202fbbe40a8d7bad19fcf1c9333dbd23e1abe6278c2989eaed61b3ed72`
- UART model: `e5b930e56597d22ae9d9a7f2242c5e930fed48a55ebc30102d45999971adc53c`

| Source path | SHA-256 | Four-core | UART |
|---|---|:---:|:---:|
| `rv64imac/RTL/data_mem_top.sv` | `2f7daf2eca7d6afc393158ca5020f78d1c6b7267da40799baa0381a1ecfa7b7c` | ✓ | ✓ |
| `rv64imac/RTL/main_mem.sv` | `a00c16dbbecaa06d5291ee60a2b521eabaa22faa4c456a74339d7ff733dbd82a` | ✓ | ✓ |
| `rv64imac/RTL/mem_shifter.sv` | `114e2cf38a3312b4db2af63bb43b851ba024ee2385bfd74ce32d6f0af1b11b27` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_64bit_adder.sv` | `331934e42f30faf956cc2559ff9042fccefedb78345677f258328f6b1504bd84` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_alu.sv` | `17f4c105a19bbb8d8dad3f82dcb21102213c41e2ee86b27562b223760a83c837` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_alu_decoder.sv` | `1aed42744611c5e26232021ef4a600dfa83736d3769a9725b52788dd686bc523` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_amo_alu.sv` | `72c173da2bdf1de3d2efdc4eca7ba5d93958a0c9c07a4c4c95ce9e7536d00236` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_booth.sv` | `1e1e3f1351155dafa5e850ea799a7bcb8e4a5c626d7852d4e6fd8df0be9ca904` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_branch_unit.sv` | `4abfcf7d99b9d643bc14c77d233da629a8cb628097bf26cb8564b5f47cc6d7b0` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_compressed_decoder.sv` | `4b56a83d916add105c705fcdfdd69ea43760ccfd27c36742fc47b3475e9f7ed9` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_csr_control_signals.sv` | `401e926e9bf0a55ba3dcfc83d1457f0ce89c3478dc493b9786e5e191848e2935` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_csr_unit.sv` | `4799af3e7173344436c06f5581d5f0a653ad4a7a7b202d5f64f89b92738dc27e` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_dcache_controller.sv` | `cd327537090ea5edfc9825dcf5e7a0d8ce8255ca68e06651ef7fa8c11589ff9c` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_dcache_memory.sv` | `9e7c378778893ea7142de6bfb78182a501ad7069f33dda8152366f501d3338f7` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_dcache_top.sv` | `5619c52ac3db82c13684878baa677b62c51f7c5f239769e94d3bafe98ad5b5f6` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_div_in.sv` | `faa57de270d8c70ce37c1a48f9b2b657d7bda97a33b30c68bbbc884c122cb449` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_div_out.sv` | `e65d50703a3684a66d444f6f617dfe17b53b964032e8662497517365198048af` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_hazard_unit.sv` | `57c43d2a13d3dad385b4929c39b5516b88a786f8f7be453abf63b5a024ca6aea` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_icache_controller.sv` | `c30d7c6f368e74dcd03ca04f22390e2e41b3532c089e2919628333c35b6635be` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_icache_memory.sv` | `ea442d4c29076bb25b6ff2d7720d69556be15faa391d66a0ba7ab2b33b9381a3` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_icache_top.sv` | `893d68739b348bb939ae71f1d005c769e868f45af52ff976a9735bda229a13ba` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_immextend.sv` | `ee3b0146456a873821df56fb9baf01aac17692258ddb01c27ec75b02411e123e` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_ldextend.sv` | `f42a025bff701e99b020adb0c806c5ed14a14efb4509cbdf716f8ea5d54cfb2b` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_main_decoder.sv` | `c70ed426cfff636ca58ac7456074916a067d0b18c6ad502589ca91d7a3d9ab58` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_main_decoder_top.sv` | `cfa7e4402b4c97f21aee9f488254877895427d4f2bfd37fcedb3b98fc8ba4341` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_mul_div.sv` | `f479630a8c862761a5ff633863c89d221cf9fa46ac612f975bf39e2522f99ac8` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_mul_div_ctrl.sv` | `5be381b331b6e19da56274aa8d5fe934336263da1c206db347ebb40f125d5654` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_mul_in.sv` | `b6e039ccc41061f4b6b04d6915f67044c5a484d4703853b712db130b85eb1e46` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_mul_out.sv` | `ca8754167ff20008e0c8876ba94379c21f49e54a9c679d1f4e3ba89b5d0b71ff` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_mux2x1.sv` | `7efbb33fbbeb7258171f87eb9d92c1774c69b7b3f8112f1016879d21cae1e7cf` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_mux3x1.sv` | `dfaf6b6e93d4a6bec111b58b18caebfacd56909714d41c304d0e2f206d84a69a` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_mux4x1.sv` | `d5a73d52290a9406fa8475458ca6ec8f10d212e154c6261a04bdaa388379045d` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_mux_2to1.sv` | `98b4d8941c461830658de78639400165807da4ae2980be9814cecf9124086161` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_non_restoring.sv` | `a8805354b8a0ee65786e6e3e29903c98a6fbf819f43f9041ed54129aa7422d41` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_pcsrc.sv` | `cecce9f34387c4ad5131baeb23304afad1af06a950dc7cdb8bd8f8926885205a` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_pipe.sv` | `fdde5d990acbd009c756b8f136233b1500f8f8da3436e513e097004adb211a15` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_rf.sv` | `e7f80a0b56b4c87868e7052328bb5a68cbf87f032a9327681d2e81b38f47a6ab` | ✓ | ✓ |
| `rv64imac/RTL/riscv_core_top.sv` | `f2639c6e17d087d3fc4019153a798fbe179ea8968187f49304f21c9f35522279` | ✓ | ✓ |
| `c930/rtl/c930_aplic.sv` | `092d26139803d41a9699bab9f5b5ac8cf4e42efe8b51270818f67a23313688ad` | ✓ | ✓ |
| `c930/rtl/c930_axi_cache_adapter.sv` | `16d051b3dcf179685fc1a6963d15d780babce5192678b7db7fd7ccd8108aa505` | ✓ | ✓ |
| `c930/rtl/c930_axi_crossbar.sv` | `7dfd3e041acef3840c16a4d4c90891d7b3dc9fc15317e8af26510312965e31b0` | ✓ | ✓ |
| `c930/rtl/c930_axi_dma_arb.sv` | `ceca53c914d1b4e5022715def27d8fbf0782f7f5444ac95e884d04e9b92e91ee` | ✓ | ✓ |
| `c930/rtl/c930_bf16_mul.sv` | `b8b148680888380044812a7930c6bfcee5c50a435c2578f8ed8fc856b156ef53` | ✓ | ✓ |
| `c930/rtl/c930_bootrom.sv` | `5ba8396b29da0e843e7eee052eeee6e3e608a049d8151154944560ff0061407b` | ✓ | ✓ |
| `c930/rtl/c930_cla_comp.sv` | `1a79344b2a596bcec47b421651d9d117f560ba4793c9e9fec634e6228ed6e4a4` | ✓ | ✓ |
| `c930/rtl/c930_cla_sub.sv` | `5e917c2c062c5031320cef97b7a8cce3b9e76936884c51de3479a8e365fad707` | ✓ | ✓ |
| `c930/rtl/c930_ddr.sv` | `a8c75bcc4f8be56330a712c80586cbddd5cf523558f931f56dd8b5f70b92c8a9` | ✓ | ✓ |
| `c930/rtl/c930_fp16_acc.sv` | `65515566b2a6e2f7cb3ac6d45f4c87510d1177d33f962127d32b0dc0b2d07244` | ✓ | ✓ |
| `c930/rtl/c930_fp16_mul.sv` | `5579104bc4f56c7f70b018387c79dc8bd68c1c36244a983d432c88ff3ba70269` | ✓ | ✓ |
| `c930/rtl/c930_fp_mul.sv` | `3d7e4e51d819d72df2914659dbb3441c7154ab40a2b70729f4cf09c09d293227` | ✓ | ✓ |
| `c930/rtl/c930_fx_acc.sv` | `35caf5d237ba087962ffc1f51309f2ef54439ecbef6a1d58279eba005595c414` | ✓ | ✓ |
| `c930/rtl/c930_l2.sv` | `adf24f914c7bb23f55b9526fed2c398017a6c5e7f809a7e918cc26db8fe77685` | ✓ | ✓ |
| `c930/rtl/c930_mmio_arb.sv` | `fd34b16e2ef34b3998c6d5f8fbbd49520a6d1ecf1746b80f6a6f3d36d4fa0922` | ✓ | ✓ |
| `c930/rtl/c930_mmio_bridge.sv` | `194b7c30d7f478a162bcfcc88aef2b68ff7410cf4c3dc20888e8c96b84e1aac4` | ✓ | ✓ |
| `c930/rtl/c930_npu_act.sv` | `bc474939f8f39f8dcde312fb47460c61fd56a09339323fdcb8a28702dc179316` | ✓ | ✓ |
| `c930/rtl/c930_npu_core.sv` | `16cc8f28e37ad8a50a01a774cc3920805db39440fbbdae8226ba66c02ee05c50` | ✓ | ✓ |
| `c930/rtl/c930_npu_csr.sv` | `afdf57313641be4b03215f3e6041a157357898837f1895a5f035141c047392cf` | ✓ | ✓ |
| `c930/rtl/c930_npu_dma.sv` | `dfd2e655d45fd58f45f0f73cc2911f6b4e2f80212ba16dfb6d713f39245ebe14` | ✓ | ✓ |
| `c930/rtl/c930_npu_top.sv` | `e5d97db452319e679553a502b70926921b4dc38e43df4367c69350e24cf43e4b` | ✓ | ✓ |
| `c930/rtl/c930_soc_top.sv` | `5a60ec2b11a816f1268a2f8852d04f57e18f7ecd59e6c43f5b7ac9d8f8d93ac3` | ✓ | ✓ |
| `c930/rtl/c930_systolic_array.sv` | `2d320fc1ba03775933b1579d32c4b32acd4cd5ae65f9a861224a6d893556787c` | ✓ | ✓ |
| `c930/rtl/c930_tensor_pe.sv` | `a2bc95a051b0a7c07931d3d424d8fa94af78067ee0eef53f2a5be99a84ce2a02` | ✓ | ✓ |
| `c930/rtl/c930_uart.sv` | `ccca326301d7b93bf83553f165f918bffe56b299b5c77285b824cc584e471806` | ✓ | ✓ |
| `c930/sim/c930_soc4_verilator.sv` | `4341ef886fa8eb46f8327033c851284c5aa171f5f450065777b8b92cc905a185` | ✓ | — |
| `c930/sim/c930_soc_verilator.sv` | `0c16fe035280cf1f3d99b4312aecdfaa0caa1fbc72b7f9723ef559854b78f917` | — | ✓ |
| `c930/sim/tb_soc4.cc` | `8425ff9727b65cf940458243ed7dc352674b67a89ea775421735aaa26d5c73eb` | ✓ | — |
| `c930/sim/tb_uart_echo.cc` | `d0888b52c8591774266f2386952fcce96bec1d98e5d43298b7de8f6dffe9dd16` | — | ✓ |

## Firmware and recorded verification evidence

| Run input / artifact | SHA-256 | Role / recorded result |
|---|---|---|
| `c930/sw/boot.hex` | `350f4980c33edd249de23aad95ff419808f6a9be1361ff13c76dedd2eda5fe05` | Four-core boot image |
| `c930/sw/tb4_phase1_fw.hex` | `670620b248fd225b9c0ff9f74d3e42b3bfb0609c683416ce89038a1d24f132ca` | Four-core suite phase 1 |
| `c930/sw/tb4_phase2_fw.hex` | `3e4b5abf1e7dbb89fb08372c21b4b91a2a76274ed20f613b66659a2eff6a4091` | Four-core suite phase 2 |
| `c930/build/e004_candidate_uart/firmware/firmware_uart_echo_test.hex` | `63750c981cfb65b6b6c45c272718823ada4642bb243826b9f9f3ba4b317d0b14` | UART echo input, archived under the earlier candidate output directory |
| `c930/build/e004_candidate_uart/firmware/firmware_uart_gemm_test.hex` | `dce77ac43de9d8a01a5b9c6c1753965e93d86332ed5d271645916b79ba675` | UART GEMM input, archived under the earlier candidate output directory; saved run reports 18/18 |
| Four-core generation log | `ef5a194e1357d9baeab57dca2462550f3cb0249c6067932b04f99e70955e8ba1` | Verilator generation/build log |
| Four-core run log | `567b6f6058c6e50672249208f274db18e76757e914098f22e92cde7fbe3463b4` | Saved suite output: both phase markers present; not a new run |
| UART generation log | `cadc0d810a836be03f481890fb18e4cb738e38ba66b4e96bb231ac923bc26435` | Verilator generation log |
| UART echo run log | `1544dd2e164bce2ffa315c884e641d69e8809c2188027c78368d9246994a056f` | Saved echo output, previously reported as passing |
| UART GEMM run log | `187f569c8e814c5ce4876a93af3149a6579a8aad1fd6f7f494f171f2e3bc5c24` | Saved output reports 18/18 cases; not a new run |
| Four-core generated-source metadata | `206193faa60d0eb2014982f5f94a47484e999c8adb50a8c9a29a5ad381049939` | Exact source/command record for suite generation |
| UART generated-source metadata | `669198fe4e0e197059215f3d7495a1b582b6c2bdd5a3bd83986d12393ba6b668` | Exact source/command record for UART generation |

## Harness diagnostics and local-change exclusions

- The four-core candidate uses `c930/sim/c930_soc4_verilator.sv` and `c930/sim/tb_soc4.cc` with hierarchical CPU/MMIO/CSR observation taps and conditional diagnostic output. Compared with canonical HEAD, the reviewed changes add observation/printing only; no simulator stimulus or DUT input changes were found. Preserve this exact harness variant for any reproduction of the recorded run.
- The UART candidate uses separate harness files, `c930/sim/c930_soc_verilator.sv` and `c930/sim/tb_uart_echo.cc`, with the per-file hashes above.
- The following files present in the separate GRX930 checkout were explicitly **not included** by the recorded E-004 invocations and are outside this approval: modified `c930/tb/tb_grx930_test_chip.sv`; untracked `c930/rtl/c930_fp16_acc_nf.sv` and `c930/rtl/c930_npu_core-1.sv`; CPU `.sv.bak` files; newly added tests/scripts; other local edits, generated outputs, and untracked build artifacts.
- The candidate does not encompass every file in either checkout. Any proposed change to the source list, firmware, harness, toolchain, or configuration requires a separately identified review input set; do not silently substitute current working-tree versions.

## What this approval means—and does not mean

This records the owner's selection of these exact snapshots for **future engineering verification**. It does not retroactively validate or independently reproduce the saved runs. E-002 and E-004 remain open until the required source/evidence reviews and independent reproduction are completed. The E-001 four-core/one-NPU scope remains a product proposal. No product, FPGA, ASIC, manufacturing, tapeout, commercial, supplier, funding, or spending decision is implied.

No source checkout, RTL file, firmware, test, build artifact, or saved run log was changed to record this approval.
