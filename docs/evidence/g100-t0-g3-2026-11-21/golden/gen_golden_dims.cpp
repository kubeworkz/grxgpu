// Generates G3 edge-shape SGEMM references.
//
// This is a dimension-parameterized copy of the frozen G2 generator. M and N
// are arguments here because the frozen generator fixes M=N=64. The seed,
// input order, FP16 conversion, and double-accumulate reference are unchanged;
// validate this copy against the frozen generator before trusting a shape.
// libc rand() is part of the input contract: run on the pinned glibc.

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
  if (argc != 5) {
    std::fprintf(stderr, "usage: gen_golden_dims <M> <N> <K> <output-prefix>\n");
    return 2;
  }

  const uint32_t M = uint32_t(std::strtoul(argv[1], nullptr, 10));
  const uint32_t N = uint32_t(std::strtoul(argv[2], nullptr, 10));
  const uint32_t K = uint32_t(std::strtoul(argv[3], nullptr, 10));
  const char* prefix = argv[4];

  if (M == 0 || N == 0 || K == 0 ||
      (M % 16) != 0 || (N % 16) != 0 || (K % 8) != 0) {
    std::fprintf(stderr,
                 "unsupported dimensions: M=%u N=%u K=%u "
                 "(M,N must be multiples of 16; K a multiple of 8)\n",
                 M, N, K);
    return 2;
  }

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
