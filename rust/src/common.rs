use std::io::{BufReader, Read, Result, Cursor};
use flate2::read::GzDecoder;
use bzip2::read::BzDecoder;

/// Create a reader with automatic compression detection
pub fn create_reader_with_compression<R: Read + Send + 'static>(
    mut reader: R,
) -> Result<BufReader<Box<dyn Read + Send>>> {
    // Peek at first few bytes to detect compression
    let mut magic_buf = [0u8; 3];
    let mut bytes_read = 0;

    // Try to read magic bytes
    while bytes_read < magic_buf.len() {
        match reader.read(&mut magic_buf[bytes_read..])? {
            0 => break, // EOF
            n => bytes_read += n,
        }
    }

    // Create appropriate decoder based on magic bytes
    let decoded_reader: Box<dyn Read + Send> = if bytes_read >= 2 && magic_buf[0] == 0x1f && magic_buf[1] == 0x8b {
        // Gzip format - make owned copy of magic bytes
        let magic_copy = magic_buf[..bytes_read].to_vec();
        let chained = Cursor::new(magic_copy).chain(reader);
        let gz_reader = GzDecoder::new(chained);
        Box::new(gz_reader)
    } else if bytes_read >= 3 && magic_buf[0] == 0x42 && magic_buf[1] == 0x5a && magic_buf[2] == 0x68 {
        // Bzip2 format - make owned copy of magic bytes
        let magic_copy = magic_buf[..bytes_read].to_vec();
        let chained = Cursor::new(magic_copy).chain(reader);
        let bz_reader = BzDecoder::new(chained);
        Box::new(bz_reader)
    } else {
        // Uncompressed - put magic bytes back
        let magic_copy = magic_buf[..bytes_read].to_vec();
        let cursor = Cursor::new(magic_copy);
        Box::new(cursor.chain(reader))
    };

    Ok(BufReader::with_capacity(64 * 1024, decoded_reader))
}