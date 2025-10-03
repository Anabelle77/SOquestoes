import json
import copy
import statistics
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plotar_gantt(execution_sequence, algo_name):
    if not execution_sequence:
        print(f"Nenhuma sequência de execução para plotar para {algo_name}.")
        return
        
    fig, gnt = plt.subplots(figsize=(15, 6))
    gnt.set_title(f'Diagrama de Gantt - {algo_name}')
    gnt.set_xlabel('Tempo (ticks)')
    gnt.set_ylabel('Processos')
    
    pids = sorted(list(set(p[2] for p in execution_sequence)), reverse=True)
    y_ticks = {pid: i * 10 for i, pid in enumerate(pids)}
    gnt.set_yticks([i * 10 for i in range(len(pids))])
    gnt.set_yticklabels(pids)
    
    gnt.grid(True, which='both', linestyle='--', linewidth=0.5)
    gnt.set_ylim(-5, len(pids) * 10)
    
    colors = plt.cm.tab20(np.linspace(0, 1, len(pids)))
    pid_colors = {pid: colors[i] for i, pid in enumerate(pids)}
    
    for start, end, pid in execution_sequence:
        duration = end - start
        gnt.broken_barh([(start, duration)], (y_ticks[pid] - 4, 8), 
                        facecolors=(pid_colors[pid]), edgecolor='black')

    plt.tight_layout()
    plt.show()

def plotar_metricas(results_list):
    if not results_list:
        print("Nenhuma métrica foi calculada para plotar.")
        return

    df = pd.DataFrame(results_list)
    df.set_index('algoritmo', inplace=True)
    

    df[['avg_wait_time', 'avg_turnaround_time']].plot(kind='bar', figsize=(14, 7), 
                                                     color={'avg_wait_time': 'skyblue', 'avg_turnaround_time': 'lightgreen'})
    plt.title('Comparação de Tempos Médios por Algoritmo')
    plt.ylabel('Tempo (ticks)')
    plt.xlabel('Algoritmo')
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()


    df['throughput'].plot(kind='bar', figsize=(14, 7), color='salmon')
    plt.title('Vazão (Processos Concluídos) por Algoritmo')
    plt.ylabel('Nº de Processos Concluídos na Janela de Tempo')
    plt.xlabel('Algoritmo')
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()



def calcular_metricas(processes_done, throughput_window, algo_name):
    if not processes_done: return {}
    
    turnaround_times = [p['completion_time'] - p['arrivaltime'] for p in processes_done]
    wait_times = [(p['completion_time'] - p['arrivaltime']) - p['bursttime'] for p in processes_done]
    
    completed_in_window = sum(1 for p in processes_done if p['completion_time'] <= throughput_window)
    
    return {
        'algoritmo': algo_name,
        'avg_wait_time': statistics.mean(wait_times),
        'avg_turnaround_time': statistics.mean(turnaround_times),
        'throughput': completed_in_window
    }


def simular_fcfs(processes_list, context_cost):
    procs_sorted = sorted(processes_list, key=lambda p: p['arrivaltime'])
    current_time = 0
    execution_sequence = []
    processes_done = []
    is_first_process = True
    for process in procs_sorted:
        if not is_first_process:
            current_time += context_cost
        start_time = max(process['arrivaltime'], current_time)
        current_time = start_time
        completion_time = start_time + process['bursttime']
        process['completion_time'] = completion_time
        processes_done.append(process)
        execution_sequence.append((start_time, completion_time, process['pid']))
        current_time = completion_time
        is_first_process = False
    return processes_done, execution_sequence

def simular_sjf(processes_list, context_cost):
    procs_to_arrive = sorted(processes_list, key=lambda p: p['arrivaltime'])
    current_time = 0
    ready_queue = []
    execution_sequence = []
    processes_done = []
    while len(processes_done) < len(processes_list):
        while procs_to_arrive and procs_to_arrive[0]['arrivaltime'] <= current_time:
            ready_queue.append(procs_to_arrive.pop(0))
        if ready_queue:
            ready_queue.sort(key=lambda p: p['bursttime'])
            current_process = ready_queue.pop(0)
            if len(processes_done) > 0:
                current_time += context_cost
            start_time = current_time
            completion_time = start_time + current_process['bursttime']
            current_process['completion_time'] = completion_time
            processes_done.append(current_process)
            execution_sequence.append((start_time, completion_time, current_process['pid']))
            current_time = completion_time
        else:
            if procs_to_arrive:
                current_time = procs_to_arrive[0]['arrivaltime']
            else:
                break
    return processes_done, execution_sequence

def simular_rr(processes_list, quantum, context_cost):
    for p in processes_list:
        p['remaining_time'] = p['bursttime']
    procs_to_arrive = sorted(processes_list, key=lambda p: p['arrivaltime'])
    processes_done = []
    ready_queue = []
    execution_sequence = []
    current_time = 0
    last_process_pid = None
    while len(processes_done) < len(processes_list):
        while procs_to_arrive and procs_to_arrive[0]['arrivaltime'] <= current_time:
            ready_queue.append(procs_to_arrive.pop(0))
        if not ready_queue:
            if procs_to_arrive:
                current_time = procs_to_arrive[0]['arrivaltime']
            else:
                break
            continue
        current_process = ready_queue.pop(0)
        if last_process_pid is not None and last_process_pid != current_process['pid']:
            current_time += context_cost
        start_time = current_time
        exec_time = min(quantum, current_process['remaining_time'])
        current_process['remaining_time'] -= exec_time
        current_time += exec_time
        execution_sequence.append((start_time, current_time, current_process['pid']))
        while procs_to_arrive and procs_to_arrive[0]['arrivaltime'] <= current_time:
            ready_queue.append(procs_to_arrive.pop(0))
        if current_process['remaining_time'] == 0:
            current_process['completion_time'] = current_time
            processes_done.append(current_process)
            last_process_pid = None
        else:
            ready_queue.append(current_process)
            last_process_pid = current_process['pid']
    return processes_done, execution_sequence


if __name__ == "__main__":
    try:
        with open('ent.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Erro: O arquivo 'ent.json' não foi encontrado. Certifique-se de que ele está na mesma pasta que o script.")
        exit()

    processes = config['workload']['processes']
    context_switch_cost = config['metadata']['contextswitchcost']
    algorithms = config['metadata']['algorithms']
    rr_quantums = config['metadata']['rrquantums']
    throughput_window = config['metadata']['throughputwindowT']
    
    results_list = []

    print("Executando simulações...")
    if "FCFS" in algorithms:
        fcfs_procs = copy.deepcopy(processes)
        fcfs_completed, fcfs_sequence = simular_fcfs(fcfs_procs, context_switch_cost)
        results_list.append(calcular_metricas(fcfs_completed, throughput_window, "FCFS"))
        plotar_gantt(fcfs_sequence, "FCFS")
    
    if "SJF" in algorithms:
        sjf_procs = copy.deepcopy(processes)
        sjf_completed, sjf_sequence = simular_sjf(sjf_procs, context_switch_cost)
        results_list.append(calcular_metricas(sjf_completed, throughput_window, "SJF"))
        plotar_gantt(sjf_sequence, "SJF (Não Preemptivo)")

    if "RR" in algorithms:
        for q in rr_quantums:
            algo_name = f"RR (q={q})"
            rr_procs = copy.deepcopy(processes)
            rr_completed, rr_sequence = simular_rr(rr_procs, q, context_switch_cost)
            results_list.append(calcular_metricas(rr_completed, throughput_window, algo_name))
            plotar_gantt(rr_sequence, algo_name)

    print("\nSimulações concluídas. Gerando gráficos de comparação de métricas.")
    plotar_metricas(results_list)

    print("\nAnálise concluída.")