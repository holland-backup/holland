"""Constants used by various bits in the LVM API"""

PVS_ATTR = [
    'pv_fmt',
    'pv_uuid',
    'pv_size',
    'dev_size',
    'pv_free',
    'pv_used',
    'pv_name',
    'pv_attr',
    'pv_pe_count',
    'pv_pe_alloc_count',
    'pv_tags',
    # segment info introduces duplicate records
    # (with differing seginfo data)
    #'pvseg_start',
    #'pvseg_size',
    'pe_start',
    'vg_name'
]

VGS_ATTR = [
    'vg_fmt',
    'vg_uuid',
    'vg_name',
    'vg_attr',
    'vg_size',
    'vg_free',
    'vg_sysid',
    'vg_extent_size',
    'vg_extent_count',
    'vg_free_count',
    'max_lv',
    'max_pv',
    'pv_count',
    'lv_count',
    'snap_count',
    'vg_seqno',
    'vg_tags'
]

LVS_ATTR = [
    'lv_uuid',
    'lv_name',
    'lv_attr',
    'lv_major',
    'lv_minor',
    'lv_kernel_major',
    'lv_kernel_minor',
    'lv_size',
    'seg_count',
    'origin',
    'snap_percent',
    'copy_percent',
    'move_pv',
    'lv_tags',
    'mirror_log',
    'modules',
    'vg_name',
    'vg_extent_size',
    'vg_extent_count',
    'vg_free_count',
]
