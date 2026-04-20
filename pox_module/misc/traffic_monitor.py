from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.recoco import Timer
import os
import time

log = core.getLogger()

CSV_HEADER = (
    "generated_at,dpid,total_flows,total_packets,total_bytes,"
    "aggregate_byte_rate_bps,top_src_ip,top_dst_ip,top_proto,"
    "top_src_port,top_dst_port,top_packets,top_bytes,top_rate_bps"
)


class TrafficMonitor(object):
    """
    Per-switch collector for OpenFlow flow statistics.
    """

    def __init__(self, connection, interval, report_file, report_every):
        self.connection = connection
        self.interval = max(1, int(interval))
        self.report_file = report_file
        self.report_every = max(1, int(report_every))
        self.prev_stats = {}
        self.poll_count = 0
        self.dpid_str = str(connection.dpid)

        connection.addListeners(self)
        self._init_report_csv_if_needed()

        self.timer = Timer(self.interval, self.request_stats, recurring=True)
        log.info("Traffic monitor attached to switch %s", self.dpid_str)

    def _init_report_csv_if_needed(self):
        if not os.path.exists(self.report_file):
            with open(self.report_file, "w") as f:
                f.write(CSV_HEADER + "\n")
            return

        with open(self.report_file, "r+") as f:
            content = f.read()
            first_line = content.splitlines()[0].strip() if content else ""

            if first_line == CSV_HEADER:
                return

            f.seek(0)
            f.write(CSV_HEADER + "\n" + content)
            f.truncate()

    def request_stats(self):
        request = of.ofp_stats_request(body=of.ofp_flow_stats_request())
        self.connection.send(request)

    def _flow_key(self, stat):
        match = stat.match
        return (
            self.dpid_str,
            str(match.nw_src) if match.nw_src is not None else "-",
            str(match.nw_dst) if match.nw_dst is not None else "-",
            int(match.nw_proto) if match.nw_proto is not None else 0,
            int(match.tp_src) if match.tp_src is not None else 0,
            int(match.tp_dst) if match.tp_dst is not None else 0,
        )

    def _append_summary_report_csv(self, flows):
        total_flows = len(flows)
        total_packets = sum(item["packets"] for item in flows)
        total_bytes = sum(item["bytes"] for item in flows)
        total_rate = sum(item["rate"] for item in flows)
        top_flow = max(flows, key=lambda x: x["bytes"]) if flows else None

        with open(self.report_file, "a") as f:
            if top_flow is None:
                f.write(
                    "{:.3f},{},{},{},{},{:.2f},-,-,0,0,0,0,0,0.00\n".format(
                        time.time(),
                        self.dpid_str,
                        total_flows,
                        total_packets,
                        total_bytes,
                        total_rate,
                    )
                )
                return

            f.write(
                "{:.3f},{},{},{},{},{:.2f},{},{},{},{},{},{},{},{:.2f}\n".format(
                    time.time(),
                    self.dpid_str,
                    total_flows,
                    total_packets,
                    total_bytes,
                    total_rate,
                    top_flow["src"],
                    top_flow["dst"],
                    top_flow["proto"],
                    top_flow["sport"],
                    top_flow["dport"],
                    top_flow["packets"],
                    top_flow["bytes"],
                    top_flow["rate"],
                )
            )

    def _handle_FlowStatsReceived(self, event):
        flows_for_report = []

        for stat in event.stats:
            if stat.packet_count == 0 and stat.byte_count == 0:
                continue

            key = self._flow_key(stat)
            prev_bytes = self.prev_stats.get(key, stat.byte_count)
            byte_rate = max(0.0, float(stat.byte_count - prev_bytes) / self.interval)
            self.prev_stats[key] = stat.byte_count

            _, src_ip, dst_ip, proto, src_port, dst_port = key

            flows_for_report.append(
                {
                    "src": src_ip,
                    "dst": dst_ip,
                    "proto": proto,
                    "sport": src_port,
                    "dport": dst_port,
                    "packets": stat.packet_count,
                    "bytes": stat.byte_count,
                    "rate": byte_rate,
                }
            )

        if flows_for_report:
            print("\n========== TRAFFIC REPORT ==========")
            print(f"Switch: {self.dpid_str}")
            print(f"Time: {time.ctime()}")

            total_packets = sum(f["packets"] for f in flows_for_report)
            total_bytes = sum(f["bytes"] for f in flows_for_report)

            print(f"Active Flows: {len(flows_for_report)}")
            print(f"Total Packets: {total_packets}")
            print(f"Total Bytes: {total_bytes}")

            # Top talkers
            top_flows = sorted(flows_for_report, key=lambda x: x["bytes"], reverse=True)[:3]

            print("\nTop Flows:")
            for f in top_flows:
                print(f'{f["src"]} -> {f["dst"]} | {f["bytes"]} bytes | {f["rate"]:.2f} B/s')
            print("====================================\n")

        self.poll_count += 1

        if self.poll_count % self.report_every == 0:
            self._append_summary_report_csv(flows_for_report)
            log.info("Updated traffic report: %s", self.report_file)


def launch(interval=5, report_file="traffic_report.csv", report_every=3):
    interval = int(interval)
    report_every = int(report_every)

    def start_switch(event):
        log.info("Switch connected: %s", event.connection.dpid)
        TrafficMonitor(
            connection=event.connection,
            interval=interval,
            report_file=report_file,
            report_every=report_every,
        )

    core.openflow.addListenerByName("ConnectionUp", start_switch)
    log.info(
        "Traffic monitor started (interval=%ss, report=%s, report_every=%s)",
        interval,
        report_file,
        report_every,
    )
