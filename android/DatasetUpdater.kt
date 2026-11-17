// Requires kotlinx-serialization-json, kotlinx-coroutines-android and OkHttp.
// Call checkAndUpdate from Dispatchers.IO. Set owner/repo and pinned tag.
package example.sudoku

import java.io.File
import java.security.MessageDigest
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.Request

@Serializable data class DatasetFile(val name: String, val count: Int, val bytes: Long, val sha256: String)
@Serializable data class DatasetManifest(val schema: Int, val version: String, val boardSize: Int, val recordBytes: Int, val format: String, val files: List<DatasetFile>)

class DatasetUpdater(private val owner: String, private val repo: String, private val dir: File) {
    private val http = OkHttpClient()
    private val json = Json { ignoreUnknownKeys = true }
    private fun fetch(url: String): ByteArray {
        val request = Request.Builder().url(url).header("Accept", "application/octet-stream").build()
        http.newCall(request).execute().use { response ->
            check(response.isSuccessful) { "HTTP ${response.code}: $url" }
            return response.body?.bytes() ?: error("Empty response")
        }
    }
    private fun sha256(data: ByteArray): String = MessageDigest.getInstance("SHA-256")
        .digest(data).joinToString("") { "%02x".format(it) }
    fun checkAndUpdate(tag: String): List<String> {
        dir.mkdirs()
        require(Regex("[A-Za-z0-9._-]+").matches(tag))
        val base = "https://github.com/$owner/$repo/releases/download/$tag/"
        val raw = fetch(base + "manifest.json")
        val manifest = json.decodeFromString<DatasetManifest>(raw.decodeToString())
        require(manifest.schema == 1 && manifest.boardSize == 16 && manifest.recordBytes == 160 && manifest.format == "S16P-v1")
        require(manifest.version == tag)
        val changed = mutableListOf<String>()
        for (entry in manifest.files) {
            require(entry.name in listOf("easy.bin", "medium.bin", "hard.bin"))
            val file = File(dir, entry.name)
            if (file.exists() && file.length() == entry.bytes && sha256(file.readBytes()).equals(entry.sha256, true)) continue
            val bytes = fetch(base + entry.name)
            check(bytes.size.toLong() == entry.bytes && sha256(bytes).equals(entry.sha256, true)) { "Checksum mismatch: ${entry.name}" }
            val tmp = File(dir, entry.name + ".tmp")
            tmp.writeBytes(bytes)
            // Atomic rename on same filesystem. Keep old file if replacement fails.
            val backup = File(dir, entry.name + ".bak")
            if (backup.exists()) backup.delete()
            if (file.exists()) check(file.renameTo(backup))
            if (!tmp.renameTo(file)) {
                if (backup.exists()) backup.renameTo(file)
                error("Could not install ${entry.name}")
            }
            backup.delete()
            changed += entry.name
        }
        return changed
    }
}
