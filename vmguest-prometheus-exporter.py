import argparse
import time

from prometheus_client import Gauge, CollectorRegistry, write_to_textfile

from vmguestlib import VMGuestLib

PROM_REGISTRY = CollectorRegistry()

VM_PROCESSOR_TIME = Gauge("vmware_vm_processor_time", "VM Processor time in percent", registry=PROM_REGISTRY)
VM_PROCESSOR_STOLEN = Gauge("vmware_vm_processor_stolen_time", "VM Percent of Stolen CPU time", registry=PROM_REGISTRY)
VM_PROCESSOR_EFECTIVE_SPEED = Gauge("vmware_vm_processor_efective_speed", "VM Qty of MHz this vm is using",
                                    registry=PROM_REGISTRY)
VM_HOST_PROCESSOR_SPEED = Gauge("vmware_host_processor_speed", "Host processor speed in MHz", registry=PROM_REGISTRY)
VM_PROCESSOR_LIMIT = Gauge("vmware_vm_processor_limit", "VM Processor Limit", registry=PROM_REGISTRY)
VM_PROCESSOR_RESERVATION = Gauge("vmware_vm_processor_reservation", "VM Processor Reservation in MHz",
                                 registry=PROM_REGISTRY)
VM_PROCESSOR_SHARES = Gauge("vmware_vm_processor_shares", "VM Processor Shares", registry=PROM_REGISTRY)

VM_MEMORY_ACTIVE = Gauge("vmware_vm_memory_active", "VM Memory used at this moment in MB", registry=PROM_REGISTRY)
VM_MEMORY_BALLONED = Gauge("vmware_vm_balloned", "VM Size of Ballon in MB", registry=PROM_REGISTRY)
VM_MEMORY_SHARED = Gauge("vmware_vm_memory_shared", "VM Shared Memory in MB", registry=PROM_REGISTRY)
VM_MEMORY_SHARED_SAVED = Gauge("vmware_vm_memory_shared_saved", "VM Shared Memory Saved in MB", registry=PROM_REGISTRY)
VM_MEMORY_SWAPPED = Gauge("vmware_vm_memory_swapped", "VM Size of Swap, in MB", registry=PROM_REGISTRY)
VM_MEMORY_TARGET_SIZE = Gauge("vmware_vm_memory_target_size", "VM Memory Target Size", registry=PROM_REGISTRY)
VM_MEMORY_USED = Gauge("vmware_vm_memory_used", "VM Memory real consumption in MB", registry=PROM_REGISTRY)
VM_MEMORY_LIMIT = Gauge("vmware_vm_memory_limit", "VM Memory Limit defined in Vcenter in MB", registry=PROM_REGISTRY)
VM_MEMORY_RESERVATION = Gauge("vmware_vm_memory_reservation", "VM Reserved Memory for this VM in MB",
                              registry=PROM_REGISTRY)
VM_MEMORY_SHARES = Gauge("vmware_vm_memory_shares", "VM Memory Share in same host", registry=PROM_REGISTRY)
VM_MEMORY_MAPPED = Gauge("vmware_vm_memory_mapped", "VM Mapped Memory", registry=PROM_REGISTRY)

GUEST_LIB = VMGuestLib()
GUEST_LIB.update_info()


def populate_memory_data():
    GUEST_LIB.update_info()
    mem_limit = GUEST_LIB.get_mem_limit_mb()

    if mem_limit == -1 & 0xFFFFFFFF:
        memory_limit = -1
    else:
        memory_limit = mem_limit

    VM_MEMORY_ACTIVE.set(GUEST_LIB.get_mem_active_mb())
    VM_MEMORY_BALLONED.set(GUEST_LIB.get_mem_ballooned_mb())
    VM_MEMORY_MAPPED.set(GUEST_LIB.get_mem_mapped_mb())
    VM_MEMORY_SHARED.set(GUEST_LIB.get_mem_shared_mb())
    VM_MEMORY_SHARED_SAVED.set(GUEST_LIB.get_mem_shared_saved_mb())
    VM_MEMORY_SWAPPED.set(GUEST_LIB.get_mem_swapped_mb())
    VM_MEMORY_TARGET_SIZE.set(GUEST_LIB.get_mem_target_size_mb())
    VM_MEMORY_USED.set(GUEST_LIB.get_mem_used_mb())
    VM_MEMORY_LIMIT.set(memory_limit)
    VM_MEMORY_RESERVATION.set(GUEST_LIB.get_mem_reservation_mb())
    VM_MEMORY_SHARES.set(GUEST_LIB.get_mem_shares())


def populate_processor_data():
    GUEST_LIB.update_info()

    old_elapsed_ms = GUEST_LIB.get_elapsed_ms()
    old_stolen_ms = GUEST_LIB.get_cpu_stolen_ms()
    old_used_ms = GUEST_LIB.get_cpu_used_ms()

    time.sleep(2)

    GUEST_LIB.update_info()
    new_elapsed_ms = GUEST_LIB.get_elapsed_ms()
    new_stolen_ms = GUEST_LIB.get_cpu_stolen_ms()
    new_used_ms = GUEST_LIB.get_cpu_used_ms()

    c = 0
    used_cpu = 0
    stolen_cpu = 0
    effective_mhz = 0
    while c < 10:
        if new_elapsed_ms == old_elapsed_ms:
            time.sleep(2)
            GUEST_LIB.update_info()
            new_elapsed_ms = GUEST_LIB.get_elapsed_ms()
            new_stolen_ms = GUEST_LIB.get_cpu_stolen_ms()
            new_used_ms = GUEST_LIB.get_cpu_used_ms()
            c += 1
        else:
            used_cpu = round((new_used_ms - old_used_ms) * 100.0 / (new_elapsed_ms - old_elapsed_ms), 2)
            stolen_cpu = round((new_stolen_ms - old_stolen_ms) * 100.0 / (new_elapsed_ms - old_elapsed_ms), 2)
            effective_mhz = round(GUEST_LIB.get_host_processor_speed() * (new_used_ms - old_used_ms) /
                                  (new_elapsed_ms - old_elapsed_ms), 2)
            break

    c_l = GUEST_LIB.get_cpu_limit_mhz()
    if c_l == -1 & 0xFFFFFFFF:
        cpu_limit = -1
    else:
        cpu_limit = c_l
    VM_PROCESSOR_TIME.set(used_cpu)
    VM_PROCESSOR_STOLEN.set(stolen_cpu)
    VM_PROCESSOR_EFECTIVE_SPEED.set(effective_mhz)
    VM_HOST_PROCESSOR_SPEED.set(GUEST_LIB.get_host_processor_speed())
    VM_PROCESSOR_LIMIT.set(cpu_limit)
    VM_PROCESSOR_RESERVATION.set(GUEST_LIB.get_cpu_reservation_mhz())
    VM_PROCESSOR_SHARES.set(GUEST_LIB.get_cpu_shares())


def populate_data():
    populate_memory_data()
    populate_processor_data()


def flush_data_to_disk():
    write_to_textfile(ARGS.output_file, PROM_REGISTRY)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output-file",
                        help="Path to file with metrics",
                        default="/etc/node-exporter/vmware.prom",
                        type=str)
    ARGS = parser.parse_args()
    populate_data()
    flush_data_to_disk()
