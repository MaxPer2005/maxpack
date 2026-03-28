#ifndef MAXPACK_H
#define MAXPACK_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// ---------------------------------------------------------------------------
// Version & Error
// ---------------------------------------------------------------------------

/// Returns pack format version number.
uint32_t sp_version(void);

/// Last error message (thread-local). Valid until next sp_* call.
/// Returns NULL if no error. Do NOT free.
const char *sp_last_error(void);

// ---------------------------------------------------------------------------
// Reader — open existing pack, random access by name or index
// ---------------------------------------------------------------------------
//
// C API supports the current unencrypted maxpack formats only:
// - wrapped current packs
// - V6 seekable packs
// Legacy layouts and encrypted archives are intentionally unsupported here.

typedef struct SpReader SpReader;

/// Open current-format pack from memory. Returns handle or NULL (check sp_last_error).
SpReader *sp_open(const uint8_t *data, size_t len);

/// Close reader and free all resources.
void sp_close(SpReader *handle);

/// Number of files. Returns -1 on error.
int64_t sp_file_count(const SpReader *handle);

/// Total original (uncompressed) bytes. Returns -1 on error.
int64_t sp_original_bytes(const SpReader *handle);

/// File name at index. Pointer valid until sp_close(). NOT null-terminated.
/// Returns 0 on success, -1 on error.
int sp_file_name(const SpReader *handle, size_t index,
                 const char **out_ptr, size_t *out_len);

/// Original file size at index. Returns -1 on error.
int64_t sp_file_size(const SpReader *handle, size_t index);

/// Read file by path (O(1) lookup). Caller must free with sp_free().
/// Returns 0 on success, -1 on error (check sp_last_error).
int sp_read(const SpReader *handle, const char *path,
            uint8_t **out_ptr, size_t *out_len);

/// Read file by index. Caller must free with sp_free().
/// Returns 0 on success, -1 on error.
int sp_read_index(const SpReader *handle, size_t index,
                  uint8_t **out_ptr, size_t *out_len);

/// Check if file exists. Returns 1 (yes), 0 (no), -1 (error).
int sp_exists(const SpReader *handle, const char *path);

/// List all paths (newline-separated). Caller must free with sp_free().
int sp_list(const SpReader *handle, uint8_t **out_ptr, size_t *out_len);

// ---------------------------------------------------------------------------
// Writer — build new pack incrementally
// ---------------------------------------------------------------------------

typedef struct SpWriter SpWriter;

/// Create writer. Returns handle or NULL.
SpWriter *sp_writer_new(void);

/// Add file from memory. Returns 0/-1.
int sp_writer_add(SpWriter *handle, const char *path,
                  const uint8_t *data, size_t len);

/// Add file from disk path (uses mmap for large files). Returns 0/-1.
int sp_writer_add_file(SpWriter *handle, const char *disk_path);

/// Finish and return current-format compressed pack bytes.
/// Consumes writer. Caller must free with sp_free().
int sp_writer_finish(SpWriter *handle, uint8_t **out_ptr, size_t *out_len);

/// Discard writer without finishing.
void sp_writer_close(SpWriter *handle);

// ---------------------------------------------------------------------------
// Batch
// ---------------------------------------------------------------------------

/// Pack files from disk paths into current-format compressed pack bytes.
/// Caller must free with sp_free().
int sp_pack(const char **paths, size_t count,
            uint8_t **out_ptr, size_t *out_len);

// ---------------------------------------------------------------------------
// Memory
// ---------------------------------------------------------------------------

/// Free buffer from sp_read, sp_read_index, sp_list, sp_writer_finish, sp_pack.
void sp_free(uint8_t *ptr, size_t len);

#ifdef __cplusplus
}
#endif

#endif // MAXPACK_H
