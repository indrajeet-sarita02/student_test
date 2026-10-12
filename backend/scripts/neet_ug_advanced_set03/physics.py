"""NEET UG (Advanced Level) - Set 01 - Physics: 45 questions."""

from __future__ import annotations

from .common import q

QUESTIONS = [
    # --- Units and Measurements -------------------------------------------
    q("Units and Measurements", "EASY",
      "The dimensional formula of Planck's constant is",
      ["[M L^2 T^-1]", "[M L^2 T^-2]", "[M L T^-1]", "[M L^2 T^-3]"], 0,
      "Energy E = h*nu, so h = E/nu = [M L^2 T^-2]/[T^-1] = [M L^2 T^-1]."),
    q("Units and Measurements", "EASY",
      "The number of significant figures in the measured value 0.00250 m is",
      ["2", "3", "4", "5"], 1,
      "Leading zeros are not significant; the trailing zero after 5 is. Hence "
      "2, 5 and the trailing 0 give three significant figures."),
    q("Units and Measurements", "MEDIUM",
      "The dimensional formula of pressure is",
      ["[M L T^-1]", "[M L^2 T^-2]", "[M L^-1 T^-2]", "[M L^-1 T^-1]"], 2,
      "Pressure = force/area = [M L T^-2]/[L^2] = [M L^-1 T^-2]."),
    q("Units and Measurements", "HARD",
      "The percentage errors in the measurement of the mass and the side of a "
      "cube are 1% and 2% respectively. The percentage error in the measured "
      "density of the cube is",
      ["3%", "5%", "7%", "9%"], 2,
      "Density = m/a^3, so the percentage error = 1% + 3(2%) = 7%."),

    # --- Kinematics --------------------------------------------------------
    q("Kinematics", "EASY",
      "A body is released from rest and falls freely. The distance covered in "
      "the first 2 s (g = 10 m/s^2) is",
      ["10 m", "40 m", "5 m", "20 m"], 3,
      "h = (1/2) g t^2 = 0.5 x 10 x 4 = 20 m."),
    q("Kinematics", "MEDIUM",
      "For a projectile launched from level ground with a fixed speed, the "
      "horizontal range is maximum when the angle of projection is",
      ["45 degrees", "30 degrees", "60 degrees", "90 degrees"], 0,
      "Range R = u^2 sin 2(theta)/g is maximum when sin 2(theta) = 1, i.e. "
      "theta = 45 degrees."),
    q("Kinematics", "MEDIUM",
      "A car starts from rest and accelerates uniformly to 20 m/s in 10 s. The "
      "distance covered is",
      ["200 m", "50 m", "100 m", "150 m"], 2,
      "v = at gives a = 2 m/s^2; s = (1/2) a t^2 = 0.5 x 2 x 100 = 100 m."),
    q("Kinematics", "HARD",
      "A boat can move at 5 m/s in still water. It is steered perpendicular to "
      "a river 100 m wide flowing at 3 m/s. The time taken to cross and the "
      "drift downstream are",
      ["25 s and 60 m", "20 s and 100 m", "20 s and 60 m", "15 s and 45 m"], 2,
      "Crossing time = width/perpendicular speed = 100/5 = 20 s; the drift = "
      "current x time = 3 x 20 = 60 m."),

    # --- Laws of Motion ----------------------------------------------------
    q("Laws of Motion", "EASY",
      "Action and reaction forces described by Newton's third law",
      ["act on the same body and cancel each other",
       "have different magnitudes but the same direction",
       "act in the same direction on the same body",
       "act on different bodies and never cancel each other"], 3,
      "The two forces act on two different bodies, so they do not cancel. Only "
      "forces acting on the same body can be added to zero."),
    q("Laws of Motion", "MEDIUM",
      "A block just begins to slide down a rough incline when the angle of "
      "inclination is 30 degrees. The coefficient of static friction is",
      ["sqrt(3)", "1/2", "1/sqrt(3)", "sqrt(3)/2"], 2,
      "At the angle of repose, mu = tan(theta) = tan 30 = 1/sqrt(3)."),
    q("Laws of Motion", "MEDIUM",
      "Masses of 5 kg and 3 kg are connected by a light string passing over a "
      "frictionless pulley. The acceleration of the system (g = 10 m/s^2) is",
      ["2.5 m/s^2", "1.25 m/s^2", "5 m/s^2", "10 m/s^2"], 0,
      "a = (m1 - m2) g / (m1 + m2) = (5 - 3)(10)/(8) = 2.5 m/s^2."),
    q("Laws of Motion", "HARD",
      "A monkey of mass 20 kg climbs up a rope with an acceleration of 2 "
      "m/s^2 (g = 10 m/s^2). The tension in the rope is",
      ["200 N", "160 N", "240 N", "40 N"], 2,
      "For upward acceleration, T = m(g + a) = 20 x (10 + 2) = 240 N."),

    # --- Work, Energy and Power -------------------------------------------
    q("Work, Energy and Power", "EASY",
      "The work done by a force F = (2i + 3j) N producing a displacement "
      "s = (3i + 4j) m is",
      ["18 J", "6 J", "12 J", "5 J"], 0,
      "W = F . s = (2)(3) + (3)(4) = 6 + 12 = 18 J."),
    q("Work, Energy and Power", "MEDIUM",
      "A body of mass 2 kg moving at 4 m/s is brought to rest by a resistive "
      "force after travelling 2 m. The magnitude of the force is",
      ["4 N", "16 N", "2 N", "8 N"], 3,
      "KE = (1/2)mv^2 = 0.5 x 2 x 16 = 16 J; by the work-energy theorem "
      "F = 16/2 = 8 N."),
    q("Work, Energy and Power", "HARD",
      "A spring of force constant 200 N/m is compressed by 0.1 m. The elastic "
      "potential energy stored in it is",
      ["1 J", "2 J", "0.5 J", "20 J"], 0,
      "U = (1/2) k x^2 = 0.5 x 200 x 0.01 = 1 J."),

    # --- Rotational Motion -------------------------------------------------
    q("Rotational Motion", "EASY",
      "The moment of inertia of a uniform rod of mass M and length L about an "
      "axis through its centre and perpendicular to its length is",
      ["M L^2 / 3", "M L^2 / 2", "M L^2", "M L^2 / 12"], 3,
      "For a thin rod about an axis through its centre, I = M L^2 / 12."),
    q("Rotational Motion", "MEDIUM",
      "If the net external torque acting on a system is zero, the quantity that "
      "remains conserved is",
      ["angular momentum", "linear momentum", "kinetic energy",
       "moment of inertia"], 0,
      "dL/dt = torque; with zero external torque the angular momentum L is "
      "constant."),
    q("Rotational Motion", "HARD",
      "A solid sphere rolls without slipping on a horizontal surface. The ratio "
      "of its rotational kinetic energy to its total kinetic energy is",
      ["5/7", "2/5", "3/5", "2/7"], 3,
      "Rotational fraction = I/(I + M R^2). For a solid sphere I = (2/5) M R^2, "
      "giving (2/5)/(7/5) = 2/7."),

    # --- Gravitation -------------------------------------------------------
    q("Gravitation", "EASY",
      "The escape velocity of a body from the surface of the Earth is "
      "independent of",
      ["mass of the body", "mass of the Earth", "radius of the Earth",
       "acceleration due to gravity at the surface"], 0,
      "v_escape = sqrt(2GM/R). The mass of the escaping body cancels out."),
    q("Gravitation", "MEDIUM",
      "If the value of g at the Earth's surface is g, then its value at a "
      "height equal to the Earth's radius R is",
      ["g/2", "g/4", "g/8", "g/9"], 1,
      "g' = g R^2/(R + h)^2. With h = R, g' = g R^2/(2R)^2 = g/4."),
    q("Gravitation", "HARD",
      "The time period of a satellite moving in a circular orbit of radius r "
      "around the Earth is proportional to",
      ["r", "r^2", "r^(3/2)", "r^(1/2)"], 2,
      "Kepler's third law gives T^2 ∝ r^3, hence T ∝ r^(3/2)."),

    # --- Mechanical Properties of Solids and Fluids ------------------------
    q("Mechanical Properties of Solids", "EASY",
      "The SI unit of Young's modulus is",
      ["N m", "N m^2", "N / m^2", "N / m"], 2,
      "Young's modulus = stress/strain; strain is dimensionless, so its unit is "
      "that of stress, N/m^2 (pascal)."),
    q("Mechanical Properties of Fluids", "MEDIUM",
      "The dimensional formula of surface tension is",
      ["[M L T^-2]", "[M L^-1 T^-2]", "[M L^2 T^-2]", "[M T^-2]"], 3,
      "Surface tension = force/length = [M L T^-2]/[L] = [M T^-2]."),
    q("Mechanical Properties of Fluids", "HARD",
      "A small sphere falls through a viscous liquid with a terminal velocity. "
      "The terminal velocity is directly proportional to",
      ["the radius r", "1/r", "the square of the radius r^2", "r^3"], 2,
      "Stokes' law gives v_t = 2 r^2 (rho - sigma) g / (9 eta), so v_t ∝ r^2."),

    # --- Thermodynamics ----------------------------------------------------
    q("Thermodynamics", "EASY",
      "According to the first law of thermodynamics, the heat supplied to a "
      "system is given by",
      ["ΔU + ΔW", "ΔU - ΔW", "ΔW - ΔU", "ΔU x ΔW"], 0,
      "First law: ΔQ = ΔU + ΔW, where ΔU is the change in internal energy and "
      "ΔW the work done by the system."),
    q("Thermodynamics", "MEDIUM",
      "During a reversible isothermal expansion of an ideal gas, the internal "
      "energy of the gas",
      ["increases", "decreases", "remains constant", "becomes zero"], 2,
      "The internal energy of an ideal gas depends only on temperature; in an "
      "isothermal process T is constant, so ΔU = 0."),
    q("Thermodynamics", "HARD",
      "A Carnot engine works between a source at 500 K and a sink at 300 K. Its "
      "efficiency is",
      ["40%", "30%", "60%", "25%"], 0,
      "eta = 1 - T_sink/T_source = 1 - 300/500 = 0.40 = 40%."),

    # --- Kinetic Theory of Gases -------------------------------------------
    q("Kinetic Theory of Gases", "EASY",
      "The rms speed of the molecules of a gas is proportional to",
      ["sqrt(T/M)", "T/M", "sqrt(M/T)", "T^2/M"], 0,
      "v_rms = sqrt(3RT/M), so it varies as sqrt(T/M), where M is the molar "
      "mass."),
    q("Kinetic Theory of Gases", "MEDIUM",
      "The number of degrees of freedom of a diatomic gas molecule at ordinary "
      "temperature is",
      ["3", "5", "6", "7"], 1,
      "A diatomic molecule has 3 translational and 2 rotational degrees of "
      "freedom, giving 5 in all."),

    # --- Oscillations and Waves --------------------------------------------
    q("Oscillations and Waves", "EASY",
      "The time period of a simple pendulum (for small oscillations) is "
      "independent of",
      ["its length", "the mass of the bob",
       "the acceleration due to gravity", "the amplitude of oscillation"], 1,
      "T = 2π sqrt(L/g); there is no dependence on the mass of the bob."),
    q("Oscillations and Waves", "MEDIUM",
      "For a particle executing simple harmonic motion, its acceleration is",
      ["constant in magnitude and direction",
       "directed away from the mean position",
       "proportional to the displacement and directed towards the mean position",
       "zero at the extreme positions of displacement"], 2,
      "In SHM a = -omega^2 x, so the acceleration is proportional to the "
      "displacement and always directed towards the mean position."),
    q("Oscillations and Waves", "HARD",
      "A plane progressive wave is represented by y = A sin(kx - omega t). The "
      "speed of the wave is",
      ["omega/k", "omega k", "k/omega", "omega + k"], 0,
      "For y = A sin(kx - omega t), the wave speed v = omega/k."),

    # --- Electrostatics ----------------------------------------------------
    q("Electrostatics", "EASY",
      "The electrostatic force between two point charges separated by a "
      "distance r varies as",
      ["1/r", "1/r^2", "r^2", "1/r^3"], 1,
      "Coulomb's law gives F = (1/4 pi epsilon_0) q1 q2 / r^2, so F ∝ 1/r^2."),
    q("Electrostatics", "MEDIUM",
      "The electric field inside a charged conductor in electrostatic "
      "equilibrium is",
      ["equal to the surface field", "directed radially outward", "zero",
       "infinite"], 2,
      "Free charges redistribute until the field inside a conductor in "
      "electrostatic equilibrium becomes zero."),
    q("Electrostatics", "HARD",
      "The energy stored in a capacitor of capacitance C charged to a potential "
      "difference V is",
      ["C V^2", "(1/2) C V^2", "2 C V^2", "(1/2) C V"], 1,
      "The stored energy is U = (1/2) C V^2."),

    # --- Current Electricity -----------------------------------------------
    q("Current Electricity", "EASY",
      "Ohm's law states that, at constant temperature, the current through a "
      "conductor is",
      ["inversely proportional to the potential difference",
       "independent of the potential difference",
       "proportional to the square of the potential difference",
       "directly proportional to the potential difference"], 3,
      "V = IR, so I ∝ V when R is constant (fixed temperature)."),
    q("Current Electricity", "MEDIUM",
      "For a metallic conductor carrying a steady current, the drift velocity "
      "of the free electrons is inversely proportional to",
      ["the current", "the length of the conductor",
       "the number density of free electrons", "the potential difference"], 2,
      "I = n A e v_d; for fixed I and A, v_d is inversely proportional to the "
      "number density n of free electrons."),
    q("Current Electricity", "HARD",
      "Two resistors of 6 ohm and 3 ohm are connected in parallel. Their "
      "equivalent resistance is",
      ["2 ohm", "9 ohm", "4.5 ohm", "1 ohm"], 0,
      "1/R = 1/6 + 1/3 = 1/2, so the equivalent resistance R = 2 ohm."),

    # --- Moving Charges and Magnetism --------------------------------------
    q("Moving Charges and Magnetism", "EASY",
      "A charged particle moving in a uniform magnetic field experiences no "
      "magnetic force when its velocity is",
      ["perpendicular to the field", "at 45 degrees to the field",
       "parallel to the field", "at 60 degrees to the field"], 2,
      "F = q v B sin(theta); the force vanishes when the velocity is parallel "
      "(or antiparallel) to the field."),
    q("Moving Charges and Magnetism", "MEDIUM",
      "A charged particle of charge q and mass m moves with speed v "
      "perpendicular to a uniform magnetic field B. The radius of its circular "
      "path is",
      ["m v / (q B)", "q B / (m v)", "m B / (q v)", "q v / (m B)"], 0,
      "Equating q v B to m v^2/r gives r = m v / (q B)."),
    q("Moving Charges and Magnetism", "HARD",
      "The cyclotron frequency of a charged particle moving in a uniform "
      "magnetic field is independent of",
      ["its charge", "its mass", "the magnetic field", "its speed"], 3,
      "f = qB/(2 pi m) depends only on q, B and m, and not on the speed of the "
      "particle."),

    # --- Electromagnetic Induction and Alternating Current -----------------
    q("Electromagnetic Induction", "EASY",
      "Lenz's law is a direct consequence of the conservation of",
      ["charge", "momentum", "energy", "mass"], 2,
      "The induced effect opposes the change producing it; otherwise energy "
      "could be created, violating conservation of energy."),
    q("Alternating Current", "MEDIUM",
      "In a series LCR circuit at resonance, the impedance of the circuit is",
      ["zero", "equal to R and minimum", "equal to R and maximum",
       "infinite"], 1,
      "At resonance X_L = X_C, so the reactances cancel and Z = R, the minimum "
      "impedance."),

    # --- Optics ------------------------------------------------------------
    q("Ray Optics", "MEDIUM",
      "Total internal reflection of light can occur when light travels",
      ["from a rarer to a denser medium at any angle",
       "from a denser to a rarer medium at any angle",
       "from a denser to a rarer medium at an angle greater than the critical "
       "angle",
       "normally from a rarer to a denser medium"], 1,
      "Total internal reflection requires travel from a denser to a rarer "
      "medium with the angle of incidence larger than the critical angle."),

    # --- Dual Nature of Matter and Radiation -------------------------------
    q("Dual Nature of Matter and Radiation", "EASY",
      "In the photoelectric effect, the maximum kinetic energy of the emitted "
      "photoelectrons depends on",
      ["the intensity of the incident light",
       "the frequency of the incident light",
       "the distance of the source",
       "the area of the metal surface"], 1,
      "Einstein's equation K_max = h*nu - phi shows that the maximum kinetic "
      "energy depends on the frequency of the light, not on its intensity."),
]
