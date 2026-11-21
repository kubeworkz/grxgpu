// Generates the frozen G2 SGEMM corpus.
//
// The generation and reference semantics mirror
// tests/regression/sgemm_tcu_wg_dxa/main.cpp at the T0 pin:
//   - std::srand(50), then fp16 values from rand()/RAND_MAX through
//     rv_ftoh_s(..., frm=0);
//   - the fp32 path of matmul_cpu(): each product is rounded to fp32,
//     accumulated in double, and the sum rounded once to fp32.
// libc rand() is part of the frozen input contract, not an implementation
// detail: run this generator on the pinned glibc identified in the manifest.

#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

#include "rvfloats.h"

static uint32_t float_bits(float value) {
  uint32_t bits;
  std::memcpy(&bits, &value, sizeof(bits));
  return bits;
}

static float bits_float(uint32_t bits) {
  float value;
  std::memcpy(&value, &bits, sizeof(value));
  return value;
}

static float half_to_float(uint16_t value) {
  return bits_float(rv_htof_s(value, 0, nullptr));
}

static uint16_t generate_fp16() {
  float value = float(std::rand()) / RAND_MAX;
  return rv_ftoh_s(float_bits(value), 0, nullptr);
}

static bool write_file(const char* path, const void* data, size_t size) {
  FILE* file = std::fopen(path, "wb");
  if (!file) {
    std::perror(path);
    return false;
  }
  bool ok = std::fwrite(data, 1, size, file) == size;
  ok = (std::fclose(file) == 0) && ok;
  return ok;
}

int main(int argc, char** argv) {
  if (argc != 3) {
    std::fprintf(stderr, "usage: gen_golden <K> <output-prefix>\n");
    return 2;
  }

  const uint32_t M = 64;
  const uint32_t N = 64;
  const uint32_t K = uint32_t(std::strtoul(argv[1], nullptr, 10));
  const char* prefix = argv[2];

  std::srand(50);

  std::vector<uint16_t> A(size_t(M) * K);
  std::vector<uint16_t> B(size_t(K) * N);
  std::vector<float> C(size_t(M) * N);

  for (size_t i = 0; i < A.size(); ++i) {
    A[i] = generate_fp16();
  }
  for (size_t i = 0; i < B.size(); ++i) {
    B[i] = generate_fp16();
  }

  for (uint32_t m = 0; m < M; ++m) {
    for (uint32_t n = 0; n < N; ++n) {
      double acc = 0.0;
      for (uint32_t k = 0; k < K; ++k) {
        float product = half_to_float(A[size_t(m) * K + k])
                      * half_to_float(B[size_t(k) * N + n]) + 0.0f;
        acc += static_cast<double>(product);
      }
      C[size_t(m) * N + n] = static_cast<float>(acc);
    }
  }

  char path[1024];
  bool ok = true;
  std::snprintf(path, sizeof(path), "%s_A.fp16", prefix);
  ok = write_file(path, A.data(), A.size() * sizeof(A[0])) && ok;
  std::snprintf(path, sizeof(path), "%s_B.fp16", prefix);
  ok = write_file(path, B.data(), B.size() * sizeof(B[0])) && ok;
  std::snprintf(path, sizeof(path), "%s_C.fp32", prefix);
  ok = write_file(path, C.data(), C.size() * sizeof(C[0])) && ok;

  std::printf("M=%u N=%u K=%u A=%zu B=%zu C=%zu words\n", M, N, K,
              A.size(), B.size(), C.size());
  return ok ? 0 : 1;
}
