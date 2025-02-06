# **README: Multi-Process Traffic Simulation**

## **Project Overview**
This Python project simulates a traffic control system using multiple processes to manage normal and priority vehicle traffic, coordinate traffic lights, and display system updates. It uses **multiprocessing** for process management and **SysV IPC message queues** for inter-process communication.



## **1. Installation & Dependencies**
Ensure you have **Python 3.8+** installed. Install the required dependencies using:

```bash
pip install -r requirements.txt
```



## **2. How to Run the Simulation**
1. **Open a terminal** and navigate to the project directory.
2. Run the following command to start the simulation:

   ```bash
   python main.py
   ```

3. The program will start multiple processes:
   - **Display Process**: Shows real-time updates on the traffic system.
   - **Traffic Lights Process**: Controls traffic light states.
   - **Normal Traffic Generator**: Simulates regular vehicle traffic.
   - **Priority Traffic Generator**: Simulates high-priority vehicles (e.g., emergency vehicles).
   - **Coordinator Process**: Manages traffic based on light states and vehicle priority.

4. Once the simulation starts, you'll see log messages updating traffic conditions.



## **3. How to Stop the Simulation**
- While the simulation is running, **press 'j'** in the terminal and hit **Enter** to safely terminate all processes and clean up resources.



## **4. File Descriptions**
| File                    | Description |
|-------------------------|-------------|
| `main.py`               | Launches and manages all processes. |
| `coordinator.py`        | Handles vehicle movement based on traffic light states. |
| `lights.py`             | Manages traffic light changes and priority overrides. |
| `display.py`           | Sets up a TCP server to display system logs. |
| `normal_traffic_gen.py` | Generates normal vehicle traffic. |
| `priority_traffic_gen.py` | Generates priority vehicles (e.g., emergency vehicles). |
| `ipc_utils.py`         | Handles message queues using SysV IPC. |
| `common.py`           | Defines shared settings like light intervals and vehicle message structures. |
| `requirements.txt`     | Lists all required Python dependencies. |



## **5. Configuration: Time Intervals in `common.py`**
You can modify the time intervals for vehicle generation and traffic light changes in `common.py`:

```python
# Time intervals (in seconds)
NORMAL_GEN_INTERVAL = 3         # Interval for generating normal vehicles
PRIORITY_GEN_INTERVAL = 21      # Interval for generating high-priority vehicles
LIGHT_CHANGE_INTERVAL = 10      # Interval for traffic light changes
```

Adjust these values to fine-tune the behavior of the traffic simulation.