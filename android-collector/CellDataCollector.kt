package com.cellsite.collector

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.location.Location
import android.os.Build
import android.telephony.*
import androidx.core.app.ActivityCompat
import com.google.android.gms.location.*
import com.google.gson.Gson
import kotlinx.coroutines.*
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.IOException
import java.util.*
import java.util.concurrent.TimeUnit

/**
 * Cell Site Data Collector Service
 * Collects cell network telemetry and GPS data for tower mapping
 * 
 * Requirements:
 * - android.permission.ACCESS_FINE_LOCATION
 * - android.permission.ACCESS_COARSE_LOCATION
 * - android.permission.READ_PHONE_STATE
 */
class CellDataCollector(
    private val context: Context,
    private val apiBaseUrl: String = "http://YOUR_BACKEND_IP:8000/api/v1"
) {
    
    private val telephonyManager: TelephonyManager =
        context.getSystemService(Context.TELEPHONY_SERVICE) as TelephonyManager
    
    private val fusedLocationClient: FusedLocationProviderClient =
        LocationServices.getFusedLocationProviderClient(context)
    
    private val deviceId: String = generateDeviceId()
    private val sessionId: String = UUID.randomUUID().toString()
    
    private val httpClient = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()
    
    private val gson = Gson()
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    
    // Queue for offline data storage
    private val dataQueue = mutableListOf<CellTelemetryData>()
    
    /**
     * Start collecting cell and location data
     * @param intervalMs Collection interval in milliseconds
     */
    fun startCollection(intervalMs: Long = 5000L) {
        if (!hasRequiredPermissions()) {
            throw SecurityException("Required permissions not granted")
        }
        
        scope.launch {
            while (isActive) {
                try {
                    collectAndUploadData()
                } catch (e: Exception) {
                    e.printStackTrace()
                }
                delay(intervalMs)
            }
        }
    }
    
    /**
     * Stop data collection
     */
    fun stopCollection() {
        scope.cancel()
        uploadQueuedData() // Upload any remaining data
    }
    
    /**
     * Collect cell info and GPS data, then upload to backend
     */
    private suspend fun collectAndUploadData() {
        // Get current location
        val location = getCurrentLocation() ?: return
        
        // Get cell info
        val cellInfo = getCurrentCellInfo() ?: return
        
        // Create telemetry data object
        val telemetryData = CellTelemetryData(
            deviceId = deviceId,
            sessionId = sessionId,
            mcc = cellInfo.mcc,
            mnc = cellInfo.mnc,
            networkType = cellInfo.networkType,
            enodebId = cellInfo.enodebId,
            cellId = cellInfo.cellId,
            physicalCellId = cellInfo.physicalCellId,
            trackingAreaCode = cellInfo.trackingAreaCode,
            frequencyBand = cellInfo.frequencyBand,
            arfcn = cellInfo.arfcn,
            bandwidthMhz = cellInfo.bandwidthMhz,
            rsrp = cellInfo.rsrp,
            rsrq = cellInfo.rsrq,
            rssi = cellInfo.rssi,
            rssnr = cellInfo.rssnr,
            cqi = cellInfo.cqi,
            latitude = location.latitude,
            longitude = location.longitude,
            gpsAccuracyMeters = location.accuracy.toDouble(),
            altitudeMeters = if (location.hasAltitude()) location.altitude else null,
            deviceTimestamp = Date().toISOString(),
            carrierName = telephonyManager.networkOperatorName,
            connectionStatus = getConnectionStatus()
        )
        
        // Try to upload immediately
        val uploaded = uploadToBackend(telemetryData)
        
        if (!uploaded) {
            // Queue for later upload if failed
            dataQueue.add(telemetryData)
        }
        
        // Try to upload queued data
        if (dataQueue.isNotEmpty()) {
            uploadQueuedData()
        }
    }
    
    /**
     * Get current GPS location using FusedLocationProvider
     */
    private suspend fun getCurrentLocation(): Location? = suspendCancellableCoroutine { continuation ->
        if (ActivityCompat.checkSelfPermission(
                context,
                Manifest.permission.ACCESS_FINE_LOCATION
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            continuation.resume(null) { }
            return@suspendCancellableCoroutine
        }
        
        val locationRequest = LocationRequest.create().apply {
            priority = LocationRequest.PRIORITY_HIGH_ACCURACY
            interval = 1000
            fastestInterval = 500
        }
        
        fusedLocationClient.getCurrentLocation(
            locationRequest.priority,
            null
        ).addOnSuccessListener { location ->
            continuation.resume(location) { }
        }.addOnFailureListener {
            continuation.resume(null) { }
        }
    }
    
    /**
     * Extract cell network information from TelephonyManager
     */
    private fun getCurrentCellInfo(): CellNetworkInfo? {
        if (ActivityCompat.checkSelfPermission(
                context,
                Manifest.permission.READ_PHONE_STATE
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            return null
        }
        
        val allCellInfo = telephonyManager.allCellInfo ?: return null
        
        // Find the registered (serving) cell
        val servingCell = allCellInfo.firstOrNull { it.isRegistered } ?: return null
        
        return when (servingCell) {
            is CellInfoLte -> extractLteInfo(servingCell)
            is CellInfoNr -> extractNrInfo(servingCell)
            else -> null
        }
    }
    
    /**
     * Extract LTE (4G) cell information
     */
    private fun extractLteInfo(cellInfo: CellInfoLte): CellNetworkInfo {
        val identity = cellInfo.cellIdentity as CellIdentityLte
        val signalStrength = cellInfo.cellSignalStrength as CellSignalStrengthLte
        
        val ci = identity.ci
        val enodebId = if (ci != CellInfo.UNAVAILABLE) ci / 256 else null
        val sectorId = if (ci != CellInfo.UNAVAILABLE) ci % 256 else null
        
        return CellNetworkInfo(
            mcc = if (identity.mccString != null) identity.mccString!!.toInt() else 515,
            mnc = if (identity.mncString != null) identity.mncString!!.toInt() else 3,
            networkType = "4G",
            enodebId = enodebId,
            cellId = ci.toLong(),
            physicalCellId = identity.pci,
            trackingAreaCode = identity.tac,
            frequencyBand = mapEarfcnToBand(identity.earfcn),
            arfcn = identity.earfcn,
            bandwidthMhz = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                identity.bandwidth / 1000
            } else null,
            rsrp = signalStrength.rsrp,
            rsrq = signalStrength.rsrq,
            rssi = signalStrength.rssi,
            rssnr = signalStrength.rssnr,
            cqi = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                signalStrength.cqi
            } else null
        )
    }
    
    /**
     * Extract 5G NR cell information
     */
    private fun extractNrInfo(cellInfo: CellInfoNr): CellNetworkInfo? {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) return null
        
        val identity = cellInfo.cellIdentity as CellIdentityNr
        val signalStrength = cellInfo.cellSignalStrength as CellSignalStrengthNr
        
        val nci = identity.nci
        val enodebId = if (nci != CellInfo.UNAVAILABLE_LONG) (nci / 4096).toInt() else null
        
        return CellNetworkInfo(
            mcc = if (identity.mccString != null) identity.mccString!!.toInt() else 515,
            mnc = if (identity.mncString != null) identity.mncString!!.toInt() else 3,
            networkType = "5G",
            enodebId = enodebId,
            cellId = nci,
            physicalCellId = identity.pci,
            trackingAreaCode = identity.tac,
            frequencyBand = mapNrarfcnToBand(identity.nrarfcn),
            arfcn = identity.nrarfcn,
            bandwidthMhz = null,
            rsrp = signalStrength.ssRsrp,
            rsrq = signalStrength.ssRsrq,
            rssi = signalStrength.dbm,
            rssnr = signalStrength.ssSinr,
            cqi = null
        )
    }
    
    /**
     * Map EARFCN to frequency band for LTE
     */
    private fun mapEarfcnToBand(earfcn: Int): String {
        return when (earfcn) {
            in 0..599 -> "B1"
            in 1200..1949 -> "B3"
            in 2400..2649 -> "B5"
            in 2750..3449 -> "B7"
            in 3450..3799 -> "B8"
            in 9210..9659 -> "B28"
            in 39650..41589 -> "B41"
            else -> "UNKNOWN"
        }
    }
    
    /**
     * Map NRARFCN to frequency band for 5G
     */
    private fun mapNrarfcnToBand(nrarfcn: Int): String {
        return when (nrarfcn) {
            in 620000..680000 -> "N78"
            else -> "UNKNOWN"
        }
    }
    
    /**
     * Get connection status
     */
    private fun getConnectionStatus(): String {
        return when (telephonyManager.dataState) {
            TelephonyManager.DATA_CONNECTED -> "CONNECTED"
            TelephonyManager.DATA_CONNECTING -> "CONNECTING"
            TelephonyManager.DATA_DISCONNECTED -> "DISCONNECTED"
            else -> "UNKNOWN"
        }
    }
    
    /**
     * Upload single telemetry data to backend
     */
    private suspend fun uploadToBackend(data: CellTelemetryData): Boolean = withContext(Dispatchers.IO) {
        try {
            val json = gson.toJson(data)
            val mediaType = "application/json; charset=utf-8".toMediaType()
            val requestBody = json.toRequestBody(mediaType)
            
            val request = Request.Builder()
                .url("$apiBaseUrl/field-logs")
                .post(requestBody)
                .build()
            
            httpClient.newCall(request).execute().use { response ->
                response.isSuccessful
            }
        } catch (e: IOException) {
            e.printStackTrace()
            false
        }
    }
    
    /**
     * Upload queued data in batch
     */
    private fun uploadQueuedData() {
        if (dataQueue.isEmpty()) return
        
        scope.launch {
            try {
                val batchData = mapOf("logs" to dataQueue.toList())
                val json = gson.toJson(batchData)
                val mediaType = "application/json; charset=utf-8".toMediaType()
                val requestBody = json.toRequestBody(mediaType)
                
                val request = Request.Builder()
                    .url("$apiBaseUrl/field-logs/batch")
                    .post(requestBody)
                    .build()
                
                httpClient.newCall(request).execute().use { response ->
                    if (response.isSuccessful) {
                        dataQueue.clear()
                    }
                }
            } catch (e: IOException) {
                e.printStackTrace()
            }
        }
    }
    
    /**
     * Check if required permissions are granted
     */
    private fun hasRequiredPermissions(): Boolean {
        return ActivityCompat.checkSelfPermission(
            context,
            Manifest.permission.ACCESS_FINE_LOCATION
        ) == PackageManager.PERMISSION_GRANTED &&
        ActivityCompat.checkSelfPermission(
            context,
            Manifest.permission.READ_PHONE_STATE
        ) == PackageManager.PERMISSION_GRANTED
    }
    
    /**
     * Generate pseudo-unique device ID
     */
    private fun generateDeviceId(): String {
        return "android_${UUID.randomUUID().toString().substring(0, 8)}"
    }
    
    /**
     * Extension function to convert Date to ISO 8601 string
     */
    private fun Date.toISOString(): String {
        val sdf = java.text.SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US)
        sdf.timeZone = TimeZone.getTimeZone("UTC")
        return sdf.format(this)
    }
}

/**
 * Data class for cell network information
 */
data class CellNetworkInfo(
    val mcc: Int,
    val mnc: Int,
    val networkType: String,
    val enodebId: Int?,
    val cellId: Long,
    val physicalCellId: Int?,
    val trackingAreaCode: Int?,
    val frequencyBand: String,
    val arfcn: Int?,
    val bandwidthMhz: Int?,
    val rsrp: Int?,
    val rsrq: Int?,
    val rssi: Int?,
    val rssnr: Int?,
    val cqi: Int?
)

/**
 * Data class for complete telemetry payload
 */
data class CellTelemetryData(
    val deviceId: String,
    val sessionId: String,
    val mcc: Int,
    val mnc: Int,
    val networkType: String,
    val enodebId: Int?,
    val cellId: Long,
    val physicalCellId: Int?,
    val trackingAreaCode: Int?,
    val frequencyBand: String,
    val arfcn: Int?,
    val bandwidthMhz: Int?,
    val rsrp: Int?,
    val rsrq: Int?,
    val rssi: Int?,
    val rssnr: Int?,
    val cqi: Int?,
    val latitude: Double,
    val longitude: Double,
    val gpsAccuracyMeters: Double?,
    val altitudeMeters: Double?,
    val deviceTimestamp: String,
    val carrierName: String?,
    val connectionStatus: String?,
    val notes: String? = null
)
