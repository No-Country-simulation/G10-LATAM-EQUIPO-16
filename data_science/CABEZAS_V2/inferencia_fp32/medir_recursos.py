"""Medición de carga, latencia y memoria del proceso de inferencia CPU."""
import argparse
import json
import os
import platform
import statistics
import time
from inferencia import Clasificador

def peak_rss_mib():
    if os.name != 'nt':
        import resource
        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return value / (1024**2 if platform.system() == 'Darwin' else 1024)
    import ctypes
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
            (n, ctypes.c_size_t) for n in ('PeakWorkingSetSize', 'WorkingSetSize',
            'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
            'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]
    value = Counters()
    value.cb = ctypes.sizeof(value)
    kernel = ctypes.windll.kernel32
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    get_info = ctypes.windll.psapi.GetProcessMemoryInfo
    get_info.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    if not get_info(kernel.GetCurrentProcess(), ctypes.byref(value), value.cb):
        raise OSError('No fue posible medir memoria')
    return value.PeakWorkingSetSize / 1024**2

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repeticiones', type=int, default=30)
    parser.add_argument('--texto', default='Hoy terminé mi diplomado y estoy muy feliz.')
    args = parser.parse_args()
    if args.repeticiones < 1:
        parser.error('repeticiones debe ser positivo')
    start = time.perf_counter()
    model = Clasificador()
    load = time.perf_counter() - start
    model.predecir(args.texto)
    times = []
    for _ in range(args.repeticiones):
        start = time.perf_counter()
        model.predecir(args.texto)
        times.append(1000 * (time.perf_counter() - start))
    print(json.dumps({'plataforma': platform.platform(), 'python': platform.python_version(),
        'threads': 1, 'repeticiones': len(times), 'carga_segundos': load,
        'latencia_mediana_ms': statistics.median(times), 'latencia_maxima_ms': max(times),
        'peak_rss_mib': peak_rss_mib(),
        'nota': 'Una instancia, CPU, texto indicado y 128 tokens máximo. No mide concurrencia ni otros servicios.'},
        ensure_ascii=False, indent=2))
