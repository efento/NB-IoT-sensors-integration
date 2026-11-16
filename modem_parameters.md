# Quectel BC660 Modem Parameters

The `Deviceinfo.txt` file contains cellular network diagnostics in the `modem.parameters` array. Each value is identified by its position in the array, starting at index `0`.

The table below describes the 22 parameter positions for the Quectel BC660 modem. Older Efento NB-IoT loggers equipped with the Quectel BC66 use a different mapping, which is not covered here.

## Parameter Mapping

| Index | Parameter Name | Description | Unit / Format | Typical Range / Valid Values | Special / Invalid Values |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **0** | `sc_EARFCN` | Serving Cell E-UTRA Absolute Radio Frequency Channel Number | Channel number | 0 – 262,143 (e.g. `6446` for Band 20) | `-1` = Unknown / not registered |
| **1** | `sc_EARFCN_offset` | Carrier frequency offset relative to channel center | Index / kHz | `12` represents 0 kHz offset | `-1` = Unknown |
| **2** | `sc_PCI` | Physical Cell ID | ID | 0 – 503 | `-1` = Unknown |
| **3** | `sc_Cell_Id` | Global Cell Identity (28-bit eNodeB ID + Cell ID) | Integer (may be displayed in hexadecimal) | 0 – 268,435,455 | `0` or `-1` = No cell selected |
| **4** | `sc_RSRP` | Reference Signal Received Power | dBm | -140 to -44 dBm (e.g. `-63` dBm = excellent) | `0` = Invalid / not measured |
| **5** | `sc_RSRQ` | Reference Signal Received Quality | dB | -20 to -3 dB (e.g. `-6` dB = very good) | `0` = Invalid / not measured |
| **6** | `sc_RSSI` | Total Received Signal Strength Indicator | dBm | -110 to -25 dBm | `0` = Invalid / not measured |
| **7** | `sc_SINR` | Signal to Interference plus Noise Ratio | dB | -10 to +30 dB | `31` = Value not detectable |
| **8** | `sc_Band` | LTE Operating Band | Band number | e.g. `20` (800 MHz), `8` (900 MHz) | `-1` = Unknown |
| **9** | `sc_TAC` | Tracking Area Code | Integer (16-bit) | 1 – 65,534 | `0` or `65535` = Invalid / None |
| **10** | `sc_ECL` | Coverage Enhancement Level | Level (0, 1, or 2) | `0`: Normal<br>`1`: Enhanced<br>`2`: Extensive | `-1` = Unknown |
| **11** | `sc_TX_PWR` | Current modem transmit power | dBm | -40 to +23 dBm (e.g. `-15` dBm) | `128` = Invalid / not available |
| **12** | `OP_MODE` | NB-IoT Operation Mode | Mode code | • `0`: In-band same PCI<br>• `1`: In-band different PCI<br>• `2`: Guard band<br>• `3`: Stand-alone | `-1` = Unknown |
| **13** | `nc_EARFCN` | Neighbor Cell EARFCN | Channel number | 0 – 262,143 | `-1` = No neighbor cell measured |
| **14** | `nc_PCI` | Neighbor Cell Physical Cell ID | ID | 0 – 503 | `-1` = No neighbor cell measured |
| **15** | `nc_RSRP` | Neighbor Cell RSRP | dBm | -140 to -44 dBm | `0` = No measurement |
| **16** | `nc_RSRQ` | Neighbor Cell RSRQ | dB | -20 to -3 dB | `0` = No measurement |
| **17** | `sleep_duration` | Time modem spent in sleep state during current cycle | 0.1 s (e.g. `10` = 1.0 s) | ≥ 0 | `0` = Negligible / not tracked |
| **18** | `Rx_time` | Active receiver RF time during current transmission cycle | 0.1 s (e.g. `7` = 0.7 s) | ≥ 0 | — |
| **19** | `Tx_time` | Active transmitter RF time during current transmission cycle | 0.1 s (e.g. `5` = 0.5 s) | ≥ 0 | — |
| **20** | `PLMN_state` | Network registration status | State code | • `0`: No PLMN selected<br>• `1`: Searching for PLMN<br>• `2`: PLMN successfully selected<br>• `3`: Unknown | — |
| **21** | `selectPLMN` | Registered Public Land Mobile Network (RPLMN) | MCC + MNC combined integer | e.g. `26002` (MCC: 260 = Poland, MNC: 02 = T-Mobile) | `0` = Not registered |

## Additional Notes

- **Special values:** Depending on the parameter, values such as `-1`, `0`, `31` or `128` can indicate unavailable or invalid measurements. Consult the corresponding table row; do not treat every zero as missing data.
- **Time units:** `sleep_duration` (index `17`), `Rx_time` (index `18`) and `Tx_time` (index `19`) are expressed in units of `0.1 s`. For example, `7` means `0.7 seconds`.
- **PLMN:** `selectPLMN` (index `21`) identifies the mobile network using its Mobile Country Code (MCC) and Mobile Network Code (MNC). For example, `26002` corresponds to Poland (`260`) and T-Mobile (`02`).
