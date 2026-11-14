<h1 align="center">Md. Al Hasan Shaikat</h1>

<p align="center">Electrical & Electronic Engineer · Power Systems & Renewable Energy<br/>Dhaka, Bangladesh</p>

<p align="center">
  <a href="mailto:alhasan.shaikat02@gmail.com"><img src="https://img.shields.io/badge/Email-D14836?style=flat-square&logo=gmail&logoColor=white" alt="Email"/></a>
  <a href="https://www.linkedin.com/in/ahshaikat/"><img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=flat-square&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iI2ZmZiI%2BPHJlY3QgeD0iMyIgeT0iOSIgd2lkdGg9IjQiIGhlaWdodD0iMTIiLz48Y2lyY2xlIGN4PSI1IiBjeT0iNC44IiByPSIyLjMiLz48cGF0aCBkPSJNMTAgOWgzLjh2MS44Yy42LTEuMSAyLTIuMSA0LTIuMSAzLjMgMCA0LjIgMi4xIDQuMiA1LjJWMjFoLTR2LTYuMmMwLTEuNS0uMy0yLjctMS45LTIuNy0xLjYgMC0yLjEgMS4yLTIuMSAyLjdWMjFoLTR6Ii8%2BPC9zdmc%2B" alt="LinkedIn"/></a>
  <a href="https://scholar.google.com/citations?user=vG7kgocAAAAJ&hl=en"><img src="https://img.shields.io/badge/Google%20Scholar-4285F4?style=flat-square&logo=googlescholar&logoColor=white" alt="Google Scholar"/></a>
  <a href="https://www.researchgate.net/profile/Al-Shaikat"><img src="https://img.shields.io/badge/ResearchGate-00CCBB?style=flat-square&logo=researchgate&logoColor=white" alt="ResearchGate"/></a>
  <!--<a href="https://sites.google.com/view/ah-shaikat/home"><img src="https://img.shields.io/badge/Website-24292F?style=flat-square&logo=googlechrome&logoColor=white" alt="Website"/></a>>
</p>

<p align="center"><img src="assets/divider.svg" width="100%" alt="Single-line diagram from a generator through a transformer and transmission line to an inverter and a solar array"></p>

I'm an Electrical & Electronic Engineering graduate from **BRAC University**, working on power systems and the grid integration of renewable energy. My research covers distribution feeder reliability, machine learning for PV systems and power electronic converters, and has led to **several peer-reviewed publications** ([Google Scholar](https://scholar.google.com/citations?user=vG7kgocAAAAJ&hl=en)).

🎯 Currently looking for **M.Sc. / Ph.D. positions in Power & Energy Systems**.

### 🛠️ Tools

**Power & energy:**
![PSS®E](https://img.shields.io/badge/PSS%C2%AEE-009999?style=flat-square)
![PowerFactory](https://img.shields.io/badge/DIgSILENT%20PowerFactory-1F4E79?style=flat-square)
![PVsyst](https://img.shields.io/badge/PVsyst-F39C12?style=flat-square)
![MATLAB](https://img.shields.io/badge/MATLAB%20%2F%20Simulink-E16737?style=flat-square)

**Programming & data:**
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Verilog](https://img.shields.io/badge/Verilog-555555?style=flat-square)
![LaTeX](https://img.shields.io/badge/LaTeX-008080?style=flat-square&logo=latex&logoColor=white)
![Git](https://img.shields.io/badge/Git-F05032?style=flat-square&logo=git&logoColor=white)

**Design & embedded:**
![AutoCAD](https://img.shields.io/badge/AutoCAD%20Electrical-E51050?style=flat-square&logo=autodesk&logoColor=white)
![Cadence](https://img.shields.io/badge/Cadence%20Virtuoso%20%2F%20Innovus-A6192E?style=flat-square)
![Proteus](https://img.shields.io/badge/Proteus-1C79C0?style=flat-square)
![Arduino](https://img.shields.io/badge/Arduino-00878F?style=flat-square&logo=arduino&logoColor=white)
![ESP32](https://img.shields.io/badge/ESP32-E7352C?style=flat-square&logo=espressif&logoColor=white)

**Industrial automation (learning):**
![Siemens PLC](https://img.shields.io/badge/Siemens%20PLC-009999?style=flat-square&logo=siemens&logoColor=white)
![VFD](https://img.shields.io/badge/VFD%20%2F%20HMI-555555?style=flat-square)

### 🔬 Research interests

- Power system analysis and reliability
- Grid integration of renewable energy
- Microgrids and standalone PV–battery systems
- Techno-economic modeling of energy systems
- FACTS devices and power electronics for the grid

### ⚡ Operate my grid

This is a live 6-bus power system, **and you are the operator**. Click **⚡ Open it** or **⚡ Close it** next to a breaker and submit the issue. A bot then:

1. switches your breaker and solves the full **AC power flow (Newton-Raphson)**,
2. lets the **overcurrent relays trip** any line above 125 % of its rating, which can cascade,
3. declares a **blackout** if the power flow diverges, then black-starts the grid,
4. redraws the diagram, adds you to the operator log, and replies with every bus voltage.

The solar farm on Bus 4 follows **today's real sunlight over Dhaka**, so the grid is relaxed at noon and stressed after sunset. Opening one line is always survivable; try two or three.

<!--LIVEGRID:START-->
<p align="center">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/live-grid-dark.svg?v=0">
  <img src="assets/live-grid-light.svg?v=0" width="100%" alt="Live 6-bus grid with current power flows, voltages and alarms"/>
</picture>
</p>

| Breaker | Line | Rating | Loading | State | Operate |
|:--:|:--:|:--:|:--:|:--:|:--:|
| **CB1** | Bus 1 ↔ Bus 2 | 150 MVA | 69% | 🟥 CLOSED | [⚡ Open it](https://github.com/AHShaikat/AHShaikat/issues/new?title=grid%7Ctoggle%7CCB1&body=Press%20%2A%2ASubmit%20new%20issue%2A%2A%20to%20send%20this%20switching%20order%20to%20the%20grid.%20A%20bot%20will%20run%20a%20Newton-Raphson%20power%20flow%20and%20reply%20in%20about%20a%20minute.) |
| **CB2** | Bus 1 ↔ Bus 3 | 150 MVA | 63% | 🟥 CLOSED | [⚡ Open it](https://github.com/AHShaikat/AHShaikat/issues/new?title=grid%7Ctoggle%7CCB2&body=Press%20%2A%2ASubmit%20new%20issue%2A%2A%20to%20send%20this%20switching%20order%20to%20the%20grid.%20A%20bot%20will%20run%20a%20Newton-Raphson%20power%20flow%20and%20reply%20in%20about%20a%20minute.) |
| **CB3** | Bus 2 ↔ Bus 3 | 100 MVA | 10% | 🟥 CLOSED | [⚡ Open it](https://github.com/AHShaikat/AHShaikat/issues/new?title=grid%7Ctoggle%7CCB3&body=Press%20%2A%2ASubmit%20new%20issue%2A%2A%20to%20send%20this%20switching%20order%20to%20the%20grid.%20A%20bot%20will%20run%20a%20Newton-Raphson%20power%20flow%20and%20reply%20in%20about%20a%20minute.) |
| **CB4** | Bus 2 ↔ Bus 4 | 120 MVA | 49% | 🟥 CLOSED | [⚡ Open it](https://github.com/AHShaikat/AHShaikat/issues/new?title=grid%7Ctoggle%7CCB4&body=Press%20%2A%2ASubmit%20new%20issue%2A%2A%20to%20send%20this%20switching%20order%20to%20the%20grid.%20A%20bot%20will%20run%20a%20Newton-Raphson%20power%20flow%20and%20reply%20in%20about%20a%20minute.) |
| **CB5** | Bus 3 ↔ Bus 5 | 110 MVA | 50% | 🟥 CLOSED | [⚡ Open it](https://github.com/AHShaikat/AHShaikat/issues/new?title=grid%7Ctoggle%7CCB5&body=Press%20%2A%2ASubmit%20new%20issue%2A%2A%20to%20send%20this%20switching%20order%20to%20the%20grid.%20A%20bot%20will%20run%20a%20Newton-Raphson%20power%20flow%20and%20reply%20in%20about%20a%20minute.) |
| **CB6** | Bus 4 ↔ Bus 5 | 120 MVA | 22% | 🟥 CLOSED | [⚡ Open it](https://github.com/AHShaikat/AHShaikat/issues/new?title=grid%7Ctoggle%7CCB6&body=Press%20%2A%2ASubmit%20new%20issue%2A%2A%20to%20send%20this%20switching%20order%20to%20the%20grid.%20A%20bot%20will%20run%20a%20Newton-Raphson%20power%20flow%20and%20reply%20in%20about%20a%20minute.) |
| **CB7** | Bus 4 ↔ Bus 6 | 130 MVA | 39% | 🟥 CLOSED | [⚡ Open it](https://github.com/AHShaikat/AHShaikat/issues/new?title=grid%7Ctoggle%7CCB7&body=Press%20%2A%2ASubmit%20new%20issue%2A%2A%20to%20send%20this%20switching%20order%20to%20the%20grid.%20A%20bot%20will%20run%20a%20Newton-Raphson%20power%20flow%20and%20reply%20in%20about%20a%20minute.) |
| **CB8** | Bus 5 ↔ Bus 6 | 100 MVA | 18% | 🟥 CLOSED | [⚡ Open it](https://github.com/AHShaikat/AHShaikat/issues/new?title=grid%7Ctoggle%7CCB8&body=Press%20%2A%2ASubmit%20new%20issue%2A%2A%20to%20send%20this%20switching%20order%20to%20the%20grid.%20A%20bot%20will%20run%20a%20Newton-Raphson%20power%20flow%20and%20reply%20in%20about%20a%20minute.) |

<sub>🔁 [Black-start: close every breaker](https://github.com/AHShaikat/AHShaikat/issues/new?title=grid%7Crestore&body=Press%20%2A%2ASubmit%20new%20issue%2A%2A%20to%20send%20this%20switching%20order%20to%20the%20grid.%20A%20bot%20will%20run%20a%20Newton-Raphson%20power%20flow%20and%20reply%20in%20about%20a%20minute.) · relays trip any line above 125% · a diverging power flow means a blackout</sub>

**Top operators:** _nobody yet: be the first operator_

| Time (Dhaka) | Operator | Order | Grid response |
|---|---|---|---|
| — | — | — | — |
<!--LIVEGRID:END-->

### ☀️ Today's sun over Dhaka

<p align="center">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/solar-today-dark.svg?v=20261114T22">
  <img src="assets/solar-today-light.svg?v=20261114T22" width="100%" alt="Today's forecast PV output for a 5 kWp rooftop array in Dhaka, with irradiance, temperature and energy totals"/>
</picture>
</p>

*Updated every 3 hours from the Open-Meteo forecast. This curve also powers the G2 solar farm in the live grid.*

<details>
<summary><b>🔧 Selected projects</b></summary>
<br/>

- **3-phase LLC resonant converter for DC distribution** (2024): simulation-based design and efficiency study
- **Single-stage 3-phase grid-connected PV system** (2023): MATLAB model, panel count and string topology
- **Incentive-based smart plastic disposal system** (final-year design project, 2022–23)
- **Physical design of a 2-bit adder** in Cadence Innovus (2023)
- **House wiring design** in AutoCAD (2024)

</details>

<details>
<summary><b>🏆 Honors & memberships</b></summary>
<br/>

- Quality Journal Publication Award (BDT 50,000), BRAC University Research Metrics Committee
- Champion, academic poster presentation on MOS-controlled thyristors
- Dean's List and VC's List, BRAC University
- Graduate Student Member, IEEE Power & Energy Society
- Graduate Student Member, Optica

</details>

<p align="center"><img src="assets/divider.svg" width="100%" alt=""></p>

<p align="center"><i>Always happy to talk about power systems, renewables, or research ideas.</i></p>

This beautiful illustration is creadted with `ai`
