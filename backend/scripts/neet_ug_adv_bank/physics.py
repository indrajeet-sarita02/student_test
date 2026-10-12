"""NEET UG (Advanced Level) - Physics master bank.

``CORE`` is the curated 45-question Set 01 paper.  Everything else is produced
by small, self-checking generators so each entry has a *computed* answer and a
unique statement.  The assembly step (``seed_neet_adv_10sets``) rotates through
this pool, so correctness here is the single source of truth.
"""

from __future__ import annotations

import math

from scripts.neet_ug_advanced_set01.physics import QUESTIONS as _CORE

from .common import merge, nq, q

CORE = list(_CORE)
GEN = []


def _n(x):
    """Compact numeric formatting for options/answers (strings pass through)."""
    if isinstance(x, str):
        return x
    if isinstance(x, float) and x.is_integer():
        x = int(x)
    if isinstance(x, int):
        return str(x)
    return f"{x:.4g}"


    return f"{x:.4g}"


def _ord(n):
    """Integer ordinal: 1 -> 1st, 2 -> 2nd, 3 -> 3rd, 4 -> 4th ..."""
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _num(topic, diff, text, value, distractors, expl, unit=""):
    GEN.append(
        nq(
            topic,
            diff,
            text,
            f"{_n(value)}{unit}",
            [f"{_n(d)}{unit}" for d in distractors],
            expl,
        )
    )


# ---------------------------------------------------------------------------
# 1. Significant figures
# ---------------------------------------------------------------------------
for value, sig in [("0.00340", 3), ("20.04", 4), ("0.020", 2), ("4.500", 4),
                   ("105.0", 4), ("0.0006", 1), ("6.02", 3), ("900.0", 4)]:
    _num("Units and Measurements", "EASY",
         f"How many significant figures are present in the measured value {value}?",
         sig, [sig + 1, sig + 2, sig + 3],
         "Leading zeros are not significant, while a trailing zero after the "
         "decimal point is significant.")

# ---------------------------------------------------------------------------
# 2. Dimensional formulae
# ---------------------------------------------------------------------------
for _quantity, _dim, _wrong in [
    ("Planck's constant", "[M L^2 T^-1]", ["[M L^2 T^-2]", "[M L T^-1]", "[M L^2 T^-3]"]),
    ("angular momentum", "[M L^2 T^-1]", ["[M L^2 T^-2]", "[M L T^-1]", "[M L^2 T^-3]"]),
    ("momentum", "[M L T^-1]", ["[M L T^-2]", "[M L^2 T^-1]", "[M L^2 T^-2]"]),
    ("pressure", "[M L^-1 T^-2]", ["[M L T^-2]", "[M L^-2 T^-2]", "[M L^-1 T^-1]"]),
    ("surface tension", "[M T^-2]", ["[M L T^-2]", "[M L^-1 T^-2]", "[M L^-2 T^-2]"]),
    ("gravitational constant", "[M^-1 L^3 T^-2]", ["[M^-1 L^2 T^-2]", "[M L^3 T^-2]", "[M L^2 T^-2]"]),
    ("coefficient of viscosity", "[M L^-1 T^-1]", ["[M L T^-1]", "[M L^-2 T^-1]", "[M L^-1 T^-2]"]),
    ("magnetic field", "[M T^-2 A^-1]", ["[M L T^-2 A^-1]", "[M T^-1 A^-1]", "[M L^2 T^-2 A^-1]"]),
    ("electric flux", "[M L^3 T^-3 A^-1]", ["[M L^2 T^-3 A^-1]", "[M L^3 T^-2 A^-1]", "[M L T^-3 A^-1]"]),
    ("universal gas constant", "[M L^2 T^-2 K^-1 mol^-1]", ["[M L^2 T^-2 K^-1]", "[M L T^-2 K^-1 mol^-1]", "[M L^2 T^-3 K^-1 mol^-1]"]),
    ("latent heat", "[L^2 T^-2]", ["[M L^2 T^-2]", "[M L T^-2]", "[L T^-2]"]),
]:
    _opts = [_dim] + _wrong
    GEN.append(q("Units and Measurements", "MEDIUM",
                 f"The dimensional formula of {_quantity} is",
                 _opts, 0,
                 f"Writing the defining equation for {_quantity} gives the dimension {_dim}."))

# ---------------------------------------------------------------------------
# 2b. Kinematics  (v = u + at)
# ---------------------------------------------------------------------------
for u, a, t in [(5, 2, 3), (10, 4, 5), (0, 3, 6), (8, -2, 4), (12, 1.5, 4),
                (20, 5, 2), (3, 2.5, 4), (15, -3, 5), (6, 0.5, 8), (25, 2, 10)]:
    v = u + a * t
    _num("Kinematics", "EASY",
         f"A body moving with initial velocity {u} m/s accelerates uniformly at "
         f"{a} m/s^2 for {t} s. Its final velocity is",
         v, [v + a, v - a, v + 2 * a], f"v = u + at = {u} + ({a})({t}).", " m/s")

# 2c. distance in nth second  s_n = u + a(2n-1)/2
for u, a, n in [(0, 2, 4), (5, 4, 3), (10, 2, 6), (2, 6, 5), (0, 10, 4), (8, 2, 7)]:
    s = u + a * (2 * n - 1) / 2
    _num("Kinematics", "MEDIUM",
         f"A body starts with velocity {u} m/s and moves with uniform acceleration "
         f"{a} m/s^2. The distance travelled in the {_ord(n)} second is",
         s, [s + 1, s - 1, s + a],
         f"s_n = u + (a/2)(2n - 1) = {u} + ({a}/2)(2({n}) - 1).", " m")

# ---------------------------------------------------------------------------
# 3. Projectiles  (g = 10 m/s^2)
# ---------------------------------------------------------------------------
for u, ang in [(20, 30), (40, 45), (30, 60), (50, 30), (10, 45), (60, 60), (25, 30)]:
    th = math.radians(ang)
    H = u * u * math.sin(th) ** 2 / 20.0
    R = u * u * math.sin(2 * th) / 10.0
    T = 2 * u * math.sin(th) / 10.0
    _num("Kinematics", "MEDIUM",
         f"A projectile is fired with speed {u} m/s at {ang} degrees to the "
         f"horizontal (g = 10 m/s^2). Its maximum height is",
         round(H, 1), [round(R, 1), round(H * 2, 1), round(H + 1, 1)],
         f"H = u^2 sin^2(theta)/(2g) = {u}^2 sin^2({ang})/20.", " m")
    _num("Kinematics", "MEDIUM",
         f"A projectile is fired with speed {u} m/s at {ang} degrees to the "
         f"horizontal (g = 10 m/s^2). Its horizontal range is",
         round(R, 1), [round(H, 1), round(R * math.sin(th) ** 2, 1), round(2 * R, 1)],
         f"R = u^2 sin(2 theta)/g = {u}^2 sin({2 * ang})/10.", " m")
    _num("Kinematics", "HARD",
         f"A projectile is fired with speed {u} m/s at {ang} degrees to the "
         f"horizontal (g = 10 m/s^2). Its time of flight is",
         round(T, 2), [round(T / 2, 2), round(T * 2, 2), round(T + 1, 2)],
         f"T = 2u sin(theta)/g = 2({u}) sin({ang})/10.", " s")

# ---------------------------------------------------------------------------
# 4. Laws of motion  (T = m(g + a); g = 10)
# ---------------------------------------------------------------------------
for m, a in [(20, 2), (10, 4), (5, 6), (30, 1), (15, 5), (40, 2), (8, 3)]:
    T = m * (10 + a)
    _num("Laws of Motion", "MEDIUM",
         f"A lift (with its contents) of mass {m} kg accelerates upward at {a} m/s^2 "
         f"(g = 10 m/s^2). The tension in the supporting cable is",
         T, [m * (10 - a), m * 10, m * (10 + a) / 2], f"T = m(g + a) = {m}(10 + {a}).", " N")

for m, a in [(20, 2), (10, 4), (30, 1), (15, 5)]:
    T = m * (10 - a)
    _num("Laws of Motion", "HARD",
         f"A lift of mass {m} kg moves downward with acceleration {a} m/s^2 "
         f"(g = 10 m/s^2). The tension in the cable is",
         T, [m * (10 + a), m * 10, m * (a + 1)], f"T = m(g - a) = {m}(10 - {a}).", " N")

# friction on incline: mu = tan(theta)
for ang in [30, 45, 60]:
    mu = round(math.tan(math.radians(ang)), 3)
    label = {30: "1/sqrt(3) (= 0.577)", 45: "1 (tan 45)", 60: "sqrt(3) (= 1.732)"}[ang]
    GEN.append(q("Laws of Motion", "MEDIUM",
                 f"A block just begins to slide down a rough plane inclined at {ang} "
                 f"degrees. The coefficient of static friction is",
                 [label, "1/2", "sqrt(3)/2", "2" if ang != 45 else "0.5"], 0,
                 f"At the angle of repose mu = tan(theta) = tan {ang} degrees."))

# ---------------------------------------------------------------------------
# 5. Work, energy and power
# ---------------------------------------------------------------------------
for m, v in [(2, 4), (5, 2), (4, 10), (1, 20), (3, 6), (10, 3)]:
    ke = 0.5 * m * v * v
    _num("Work, Energy and Power", "EASY",
         f"The kinetic energy of a body of mass {m} kg moving with speed {v} m/s is",
         ke, [ke + m, ke - m, ke * 2], f"KE = (1/2)mv^2 = 0.5 x {m} x {v}^2.", " J")

for F, d, ang in [(10, 5, 0), (20, 4, 60), (8, 10, 0), (50, 2, 0), (12, 5, 0)]:
    W = F * d * math.cos(math.radians(ang))
    _num("Work, Energy and Power", "MEDIUM",
         f"A force of {F} N acts on a body through {d} m, making {ang} degrees with "
         f"the displacement. The work done is",
         round(W, 2), [round(W * 2, 2), round(W / 2, 2), round(W + F, 2)],
         f"W = F d cos(theta) = {F} x {d} x cos({ang}).", " J")

for m, h in [(2, 10), (5, 4), (10, 2), (1, 20)]:
    P = m * 10 * h  # lifting per... P = mgh, treat as energy
    _num("Work, Energy and Power", "MEDIUM",
         f"A pump lifts {m} kg of water through a height of {h} m in 1 s "
         f"(g = 10 m/s^2). Its power output is",
         P, [P / 2, P * 2, m * h], f"P = mgh/t = {m} x 10 x {h} / 1.", " W")

# ---------------------------------------------------------------------------
# 6. Rotational motion (curated formulae) and rolling
# ---------------------------------------------------------------------------
for body, Iexpr in [("solid sphere", "2/5 MR^2"), ("hollow sphere", "2/3 MR^2"),
                    ("solid cylinder", "1/2 MR^2"), ("ring", "MR^2"),
                    ("disc", "1/2 MR^2")]:
    _correct = Iexpr
    _wrong = [x for _b, x in [("solid sphere", "2/5 MR^2"), ("hollow sphere", "2/3 MR^2"),
                              ("solid cylinder", "1/2 MR^2"), ("ring", "MR^2"),
                              ("disc", "1/2 MR^2")] if x != _correct]
    GEN.append(q("Rotational Motion", "EASY",
                 f"The moment of inertia of a uniform {body} of mass M and radius R "
                 f"about its central axis is",
                 [_correct] + _wrong[:3], 0,
                 f"The standard result for a {body} about a central axis is I = {_correct}."))

for body, Icoef in [("solid sphere", 2 / 5), ("hollow sphere", 2 / 3),
                    ("solid cylinder", 1 / 2), ("ring", 1.0)]:
    a = 10 * math.sin(math.radians(30)) / (1 + Icoef)
    _num("Rotational Motion", "HARD",
         f"A {body} rolls without slipping down an incline of 30 degrees "
         f"(g = 10 m/s^2). Its linear acceleration is",
         round(a, 2), [round(10 * math.sin(math.radians(30)), 2), round(a / 2, 2), round(a + 1, 2)],
         f"a = g sin(theta)/(1 + I/MR^2) = 5/(1 + {round(Icoef, 3)}).", " m/s^2")

# ---------------------------------------------------------------------------
# 7. Gravitation
# ---------------------------------------------------------------------------
for hf in [0.01, 0.02, 0.005]:
    change = round(2 * hf * 100, 1)
    _num("Gravitation", "HARD",
         f"If the radius of the earth shrinks by {hf * 100:g}% with its mass unchanged, "
         f"g at the surface changes by about",
         f"+{change}%", [f"-{change}%", f"+{round(hf * 100, 1)}%", "0%"],
         "g = GM/R^2, so dg/g = -2 (dR/R). A decrease in R raises g.", "")

# ---------------------------------------------------------------------------
# 8. Mechanical properties of fluids
# ---------------------------------------------------------------------------
for rho, h in [(1000, 10), (1000, 5), (800, 10), (13600, 0.76)]:
    P = rho * 10 * h
    _num("Mechanical Properties of Fluids", "MEDIUM",
         f"The gauge pressure at a depth of {h} m in a liquid of density {rho} kg/m^3 "
         f"(g = 10 m/s^2) is",
         P, [P / 2, P * 2, rho * h], f"P = rho g h = {rho} x 10 x {h}.", " Pa")

for r, T in [(0.01, 0.07), (0.02, 0.07), (0.005, 0.07)]:
    P = round(4 * T / r, 1)
    _num("Mechanical Properties of Fluids", "HARD",
         f"The excess pressure inside a soap bubble of radius {r} m is "
         f"(surface tension = {T} N/m)",
         P, [round(2 * T / r, 1), round(T / r, 1), round(8 * T / r, 1)],
         "A soap bubble has two surfaces, so excess pressure = 4T/r.", " Pa")

# ---------------------------------------------------------------------------
# 9. Thermal properties / calorimetry
# ---------------------------------------------------------------------------
for m, c, dt in [(2, 4200, 10), (1, 900, 20), (5, 500, 4), (0.5, 4200, 20)]:
    Q = m * c * dt
    _num("Thermal Properties of Matter", "MEDIUM",
         f"The heat required to raise the temperature of {m} kg of a substance "
         f"(specific heat {c} J/kg/K) by {dt} K is",
         Q, [Q / 2, Q * 2, m * c], f"Q = m c dT = {m} x {c} x {dt}.", " J")

for m, L in [(2, 3.34e5), (1, 2.26e6), (0.5, 3.34e5)]:
    Q = m * L
    _num("Thermal Properties of Matter", "MEDIUM",
         f"The heat required to melt {m} kg of ice at 0 degrees C is (latent heat "
         f"of fusion = {L:g} J/kg)",
         f"{Q:.3g}", [f"{Q / 2:.3g}", f"{Q * 2:.3g}", f"{Q * 0.75:.3g}"],
         f"Q = m L = {m} x {L:g} J.", " J")

# ---------------------------------------------------------------------------
# 10. Thermodynamics
# ---------------------------------------------------------------------------
for Q_, W in [(100, 40), (200, 80), (150, 50), (300, 120)]:
    dU = Q_ - W
    _num("Thermodynamics", "EASY",
         f"A system absorbs {Q_} J of heat and does {W} J of work. The change in "
         f"its internal energy is",
         dU, [Q_ + W, W - Q_, Q_], f"dU = Q - W = {Q_} - {W}.", " J")

for T1, T2 in [(500, 300), (600, 400), (400, 300), (1000, 500)]:
    eta = round((1 - T2 / T1) * 100, 1)
    _num("Thermodynamics", "MEDIUM",
         f"A Carnot engine operates between {T1} K and {T2} K. Its efficiency is",
         f"{eta}%", [f"{round(eta / 2, 1)}%", f"{round(eta / 3, 1)}%", f"{round(eta * 2, 1)}%"],
         f"eta = 1 - T2/T1 = 1 - {T2}/{T1}.", "")

# ---------------------------------------------------------------------------
# 11. Kinetic theory
# ---------------------------------------------------------------------------
for T, M in [(300, 32), (273, 28), (400, 2), (300, 44)]:
    vrms = math.sqrt(3 * 8.314 * T / (M / 1000.0))
    _num("Kinetic Theory of Gases", "HARD",
         f"The rms speed of {M} g/mol gas molecules at {T} K is "
         f"(R = 8.314 J/mol/K), approximately",
         round(vrms, 0), [round(vrms * math.sqrt(3 / 2), 0), round(vrms / 2, 0), round(vrms * 2, 0)],
         f"v_rms = sqrt(3RT/M); M must be in kg/mol.", " m/s")

# ---------------------------------------------------------------------------
# 12. Oscillations
# ---------------------------------------------------------------------------
for m, k in [(1, 100), (4, 400), (0.5, 50), (2, 200)]:
    T = 2 * math.pi * math.sqrt(m / k)
    _num("Oscillations", "MEDIUM",
         f"A block of mass {m} kg is attached to a spring of force constant {k} N/m. "
         f"Its period of oscillation is",
         round(T, 3), [round(T / 2, 3), round(2 * T, 3), round(1.5 * T, 3)],
         f"T = 2 pi sqrt(m/k) = 2 pi sqrt({m}/{k}).", " s")

for l in [1.0, 0.5, 2.0, 1.5]:
    T = 2 * math.pi * math.sqrt(l / 10.0)
    _num("Oscillations", "EASY",
         f"The time period of a simple pendulum of length {l} m (g = 10 m/s^2) is",
         round(T, 2), [round(T / 2, 2), round(2 * T, 2), round(1.5 * T, 2)],
         f"T = 2 pi sqrt(l/g) = 2 pi sqrt({l}/10).", " s")

# ---------------------------------------------------------------------------
# 13. Waves
# ---------------------------------------------------------------------------
for f, lam in [(500, 0.68), (200, 1.7), (1000, 0.34), (50, 6.8)]:
    v = f * lam
    _num("Waves", "EASY",
         f"A wave of frequency {f} Hz has wavelength {lam} m. Its speed is",
         round(v, 1), [round(f / lam, 1), round(lam / f, 3), round(v * 2, 1)],
         f"v = f lambda = {f} x {lam}.", " m/s")

for f1, f2 in [(512, 508), (256, 260), (340, 344), (1000, 996)]:
    b = abs(f1 - f2)
    _num("Waves", "MEDIUM",
         f"Two tuning forks of frequencies {f1} Hz and {f2} Hz are sounded together. "
         f"The number of beats heard per second is",
         b, [f1 + f2, b * 2, abs(b - 1)], f"Beat frequency = |f1 - f2| = |{f1} - {f2}|.", " Hz")

# ---------------------------------------------------------------------------
# 14. Electrostatics
# ---------------------------------------------------------------------------
K = 9e9
for q1, q2, r in [(1e-6, 1e-6, 0.1), (2e-6, 3e-6, 0.3), (4e-6, 1e-6, 0.2)]:
    F = K * q1 * q2 / (r * r)
    _num("Electrostatics", "MEDIUM",
         f"Two point charges {q1:g} C and {q2:g} C are {r} m apart in vacuum. The "
         f"force between them is (k = 9 x 10^9 N m^2/C^2)",
         f"{F:.3g}", [f"{F / 2:.3g}", f"{F * 2:.3g}", f"{K * q1 * q2:.3g}"],
         f"F = k q1 q2 / r^2 = 9e9 x {q1:g} x {q2:g} / {r}^2.", " N")

for Q, V in [(2e-6, 100), (5e-6, 200), (1e-6, 50)]:
    C = Q / V
    _num("Electrostatics", "MEDIUM",
         f"A capacitor stores a charge of {Q:g} C when the potential difference "
         f"across it is {V} V. Its capacitance is",
         f"{C:.3g}", [f"{Q * V:.3g}", f"{C * 2:.3g}", f"{C / 2:.3g}"],
         f"C = Q/V = {Q:g}/{V}.", " F")

for C, V in [(2e-6, 100), (4e-6, 50), (10e-6, 12)]:
    E = 0.5 * C * V * V
    _num("Electrostatics", "HARD",
         f"The energy stored in a capacitor of capacitance {C:g} F charged to "
         f"{V} V is",
         f"{E:.3g}", [f"{C * V:.3g}", f"{E * 2:.3g}", f"{0.5 * C * V:.3g}"],
         f"U = (1/2) C V^2 = 0.5 x {C:g} x {V}^2.", " J")

# ---------------------------------------------------------------------------
# 15. Current electricity
# ---------------------------------------------------------------------------
for V, R in [(12, 4), (6, 3), (220, 110), (10, 2)]:
    I = V / R
    _num("Current Electricity", "EASY",
         f"A resistor of {R} ohm is connected across a {V} V battery. The current "
         f"through it is",
         I, [V * R, R / V, I * 2], f"I = V/R = {V}/{R}.", " A")

for I, R in [(2, 5), (3, 4), (0.5, 100), (10, 2)]:
    P = I * I * R
    _num("Current Electricity", "MEDIUM",
         f"The power dissipated in a {R} ohm resistor carrying a current of {I} A is",
         P, [P / 2, P * 2, P + I], f"P = I^2 R = {I}^2 x {R}.", " W")

for rho, L, A in [(1.7e-8, 2, 1e-6), (1.0e-7, 1, 1e-6), (2.0e-8, 5, 2e-6)]:
    R = rho * L / A
    _num("Current Electricity", "HARD",
         f"A wire of resistivity {rho:g} ohm m, length {L} m and cross-section "
         f"{A:g} m^2 has a resistance of",
         f"{R:.3g}", [f"{rho * A / L:.3g}", f"{R * 2:.3g}", f"{rho * L:.3g}"],
         f"R = rho L / A = {rho:g} x {L} / {A:g}.", " ohm")

# ---------------------------------------------------------------------------
# 16. Moving charges and magnetism
# ---------------------------------------------------------------------------
for B, v, q_ in [(2, 3, 0.5), (0.5, 10, 1), (1, 4, 2)]:
    F = B * q_ * v  # for theta = 90
    _num("Moving Charges and Magnetism", "MEDIUM",
         f"A charge of {q_:g} C moves with speed {v} m/s perpendicular to a magnetic "
         f"field of {B} T. The force on it is",
         F, [B * q_ * v / 2, B * q_ * v * 2, B * q_], f"F = qvB sin(90) = qvB.", " N")

# ---------------------------------------------------------------------------
# 17. Electromagnetic induction
# ---------------------------------------------------------------------------
for B, l, v in [(0.5, 2, 10), (1, 1, 5), (0.2, 5, 4)]:
    E = B * l * v
    _num("Electromagnetic Induction", "MEDIUM",
         f"A rod of length {l} m moves with speed {v} m/s perpendicular to a "
         f"magnetic field of {B} T. The motional emf induced is",
         E, [E / 2, E * 2, B * l], f"E = B l v = {B} x {l} x {v}.", " V")

# ---------------------------------------------------------------------------
# 18. Alternating current
# ---------------------------------------------------------------------------
for I0 in [10, 5, 2]:
    Irms = I0 / math.sqrt(2)
    _num("Alternating Current", "MEDIUM",
         f"An alternating current has a peak value of {I0} A. Its rms value is",
         round(I0 / math.sqrt(2), 2), [I0, round(I0 / 2, 2), round(I0 * math.sqrt(2), 2)],
         f"I_rms = I0/sqrt(2) = {I0}/1.414.", " A")

# ---------------------------------------------------------------------------
# 19. Ray optics
# ---------------------------------------------------------------------------
for n in [1.5, 1.33, 2.0, 1.5]:
    C = math.degrees(math.asin(1 / n))
    _num("Ray Optics", "HARD",
         f"The critical angle for total internal reflection in a medium of "
         f"refractive index {n} (w.r.t. air) is",
         round(C, 1), [round(math.degrees(math.asin(1.0 / (n * 1.5))), 1), round(90 - C, 1), round(C / 2, 1)],
         f"sin C = 1/n = 1/{n}.", " degrees")

for u, f in [(-30, 10), (-20, 20), (-15, 10), (-45, 15)]:
    inv_v = 1 / f - 1 / u
    v = 1 / inv_v
    _num("Ray Optics", "HARD",
         f"An object is placed {abs(u)} cm from a concave mirror of focal length "
         f"{f} cm. The image distance is",
         round(abs(v), 1), [round(abs(v) / 2, 1), round(abs(v) * 2, 1), round(abs(v) + 5, 1)],
         "Use 1/v + 1/u = 1/f with the sign convention for mirror distances.", " cm")

# ---------------------------------------------------------------------------
# 19b. Wave optics
# ---------------------------------------------------------------------------
for lam, D, d in [(600e-9, 1.0, 1e-3), (500e-9, 1.5, 0.5e-3), (700e-9, 2.0, 0.4e-3)]:
    beta = lam * D / d
    _num("Wave Optics", "HARD",
         f"In Young's double-slit experiment the slit separation is {d:g} m and the "
         f"screen is {D} m away. For light of wavelength {lam:g} m the fringe width is",
         f"{beta:.3g}", [f"{beta * 2:.3g}", f"{beta / 2:.3g}", f"{beta + d:.3g}"],
         f"beta = lambda D / d = {lam:g} x {D} / {d:g}.", " m")

# ---------------------------------------------------------------------------
# 20. Dual nature of matter and radiation
# ---------------------------------------------------------------------------
_h = 6.63e-34
for lam in [400e-9, 500e-9, 200e-9]:
    E = _h * 3e8 / lam
    eV = E / 1.6e-19
    _num("Dual Nature of Radiation and Matter", "HARD",
         f"The energy of a photon of wavelength {lam:g} m is "
         f"(h = 6.63 x 10^-34 J s, c = 3 x 10^8 m/s), approximately",
         f"{E:.3g}", [f"{E * 2:.3g}", f"{E / 2:.3g}", f"{_h * 3e8:.3g}"],
         f"E = hc/lambda = 6.63e-34 x 3e8 / {lam:g}.", " J")

for m, K in [(9.1e-31, 3.2e-18), (1.67e-27, 1e-13)]:
    p = math.sqrt(2 * m * K)
    lam = _h / p
    _num("Dual Nature of Radiation and Matter", "HARD",
         f"The de Broglie wavelength of a particle of mass {m:g} kg moving with "
         f"kinetic energy {K:g} J is (h = 6.63 x 10^-34 J s), approximately",
         f"{lam:.3g}", [f"{lam * 2:.3g}", f"{lam / 2:.3g}", f"{_h / (2 * _h):.3g}"],
         "lambda = h/sqrt(2mK).", " m")

# ---------------------------------------------------------------------------
# 21. Atoms (Bohr model)
# ---------------------------------------------------------------------------
for n in [1, 2, 3, 4]:
    E = -13.6 / (n * n)
    _num("Atoms", "MEDIUM",
         f"The energy of the electron in the n = {n} orbit of a hydrogen atom is",
         f"{E:.2f} eV", [f"{E * 2:.2f} eV", f"{E * 3:.2f} eV", f"{E / 2:.2f} eV"],
         f"E_n = -13.6/n^2 = -13.6/{n}^2 eV.", "")

# ---------------------------------------------------------------------------
# 22. Nuclei (half-life)
# ---------------------------------------------------------------------------
for t, T in [(2, 1), (4, 2), (9, 3), (5, 1)]:
    frac = (1 / 2) ** (t / T)
    _num("Nuclei", "HARD",
         f"A radioactive sample has a half-life of {T} h. The fraction of nuclei "
         f"remaining undecayed after {t} h is",
         f"{frac:.4g}", [f"{1 - frac:.4g}", f"{frac / 2:.4g}", f"{frac * 2:.4g}"],
         f"N/N0 = (1/2)^(t/T) = (1/2)^({t}/{T}).", "")


QUESTIONS = merge(CORE, GEN)
