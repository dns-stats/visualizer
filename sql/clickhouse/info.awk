BEGIN { FS = ":"; OFS = "\t" }
/Total Packets processed/ { total_packets = $2 + 0; }
/Malformed DNS packets/ { malformed_packets = $2 + 0; }
/Non-DNS packets/ { non_dns_packets = $2 + 0; }
/File duration/ { file_duration = $2; }
/Collection started/ { collection_started = $2; }
/Earliest data/ { earliest_data = $2; }
END {
    duration = 300;
    # If they exist, we expect durations to be 0000s9999u.
    # Report duration in s, round up if us >= 500000 or s = 0.
    # Obtain duration from file duration if present. If not, default to 300s.
    if ( length(file_duration) > 0 ) {
            spos = index(file_duration, "s");
            upos = index(file_duration, "us");
            if ( spos > 0 && upos == length(file_duration) - 1 ) {
                secs = substr(file_duration, 1, spos - 1) + 0;
                usecs = substr(file_duration, spos + 1, upos - spos - 1) + 0;
                if ( usecs > 500000 || secs == 0 )
                    secs++;
                duration = secs;
            }
        }
    if ( length(collection_started) == 0 ) {
        collection_started = earliest_data;
    }
    if ( length(collection_started) < 20 ) {
        exit 1
    }
    split(collection_started, start, " ")
    date = start[1];
    time = substr(start[2], 1, 2) ":" substr(start[2], 4, 2) ":" substr(start[2], 7, 2);
    print date, date " " time, node_id, total_packets, malformed_packets, non_dns_packets, duration;
}
