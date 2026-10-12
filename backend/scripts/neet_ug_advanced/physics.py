"""NEET UG (Advanced Level) - Physics: 45 questions."""

from __future__ import annotations

from .common import q

QUESTIONS = [
    # --- Units and Measurements -------------------------------------------
    q("Units and Measurements", "EASY",
      "The dimensional formula of Planck's constant is",
      ["[M L^2 T^-1]", "[M L^2 T^-2]", "[M L T^-1]", "[M L^2 T^-3]"], 0,
      "Energy E = h*nu, so h = E/nu = [M L^2 T^-2]/[T^-1] = [M L^2 T^-1]."),
    q("Units and Measurements", "MEDIUM",
      "Which of the following is a dimensionless physical quantity?",
      ["Strain", "Stress", "Young's modulus", "Surface tension"], 0,
      "Strain = change in dimension / original dimension, a ratio of two like "
      "quantities, so it is dimensionless."),

    # --- Kinematics --------------------------------------------------------
    q("Kinematics", "EASY",
      "A body is thrown vertically upward with speed u. Neglecting air "
      "resistance, the maximum height reached is",
      ["u^2/2g", "u^2/g", "u^2/4g", "2u^2/g"], 0,
      "Using v^2 = u^2 - 2gh and setting v = 0 at the highest point gives "
      "h = u^2/2g."),
    q("Kinematics", "MEDIUM",
      "For a projectile launched from level ground, the horizontal range is the "
      "same for projection angles 30 degrees and",
      ["60 degrees", "45 degrees", "50 degrees", "15 degrees"], 0,
      "Complementary angles of projection (summing to 90 degrees) give equal "
      "ranges; 90 - 30 = 60 degrees."),
    q("Kinematics", "HARD",
      "A particle moves along a circular path with constant speed. Its "
      "acceleration",
      ["is directed towards the centre and equals v^2/r",
       "is zero because the speed is constant",
       "is directed away from the centre and equals v^2/r",
       "is tangential to the path and equals v^2/r"], 0,
      "The speed is constant, so there is no tangential acceleration; the "
      "changing direction of velocity gives centripetal acceleration v^2/r "
      "directed towards the centre."),

    # --- Laws of Motion ----------------------------------------------------
    q("Laws of Motion", "MEDIUM",
      "A block just begins to slide down a rough inclined plane when the angle "
      "of inclination is 30 degrees. The coefficient of static friction is",
      ["1/sqrt(3)", "sqrt(3)", "1/2", "sqrt(3)/2"], 0,
      "At the angle of repose, mu = tan(theta) = tan 30 = 1/sqrt(3)."),
    q("Laws of Motion", "HARD",
      "A monkey of mass 20 kg climbs a rope with an acceleration of 2 m/s^2 "
      "(g = 10 m/s^2). The tension in the rope is",
      ["240 N", "200 N", "160 N", "40 N"], 0,
      "For upward acceleration, T = m(g + a) = 20(10 + 2) = 240 N."),

    # --- Work, Energy and Power -------------------------------------------
    q("Work, Energy and Power", "EASY",
      "The work done by a force F = (2i + 3j) N in producing a displacement "
      "s = (3i + 4j) m is",
      ["18 J", "12 J", "6 J", "5 J"], 0,
      "W = F.s = (2)(3) + (3)(4) = 6 + 12 = 18 J."),
    q("Work, Energy and Power", "MEDIUM",
      "A body of mass 2 kg moving at 4 m/s is brought to rest by a resistive "
      "force in a distance of 2 m. The magnitude of the force is",
      ["8 N", "4 N", "16 N", "2 N"], 0,
      "Kinetic energy = (1/2)mv^2 = 0.5*2*16 = 16 J. By the work-energy "
      "theorem, F*d = 16 J, so F = 16/2 = 8 N."),

    # --- Rotational Motion -------------------------------------------------
    q("Rotational Motion", "EASY",
      "The moment of inertia of a uniform rod of mass M and length L about an "
      "axis through one end and perpendicular to its length is",
      ["ML^2/3", "ML^2/12", "ML^2/2", "ML^2"], 0,
      "Using the parallel-axis theorem: ML^2/12 + M(L/2)^2 = ML^2/3."),
    q("Rotational Motion", "HARD",
      "A solid sphere and a hollow sphere of the same mass and radius roll "
      "down an incline without slipping. The ratio of their linear "
      "accelerations (solid : hollow) is",
      ["25:21", "21:25", "5:7", "7:5"], 0,
      "a = g sin(theta)/(1 + I/MR^2). Solid sphere: I = 2/5 MR^2 gives a = 5g sin "
      "theta/7; hollow sphere: I = 2/3 MR^2 gives a = 3g sin theta/5. Ratio = "
      "(5/7)/(3/5) = 25/21."),
    q("Rotational Motion", "EASY",
      "The angular momentum of a rotating system about a fixed axis is "
      "conserved when",
      ["the net external torque on it is zero",
       "the net external force on it is zero",
       "its kinetic energy is constant",
       "its linear momentum is zero"], 0,
      "Since dL/dt = torque_ext, the angular momentum stays constant when the "
      "net external torque vanishes."),

    # --- Gravitation -------------------------------------------------------
    q("Gravitation", "MEDIUM",
      "If the radius of the earth were to shrink by 1% with its mass unchanged, "
      "the value of g at the surface would",
      ["increase by about 2%", "decrease by about 2%",
       "increase by about 1%", "remain unchanged"], 0,
      "g = GM/R^2, so dg/g = -2(dR/R) = +2%. A 1% decrease in R raises g by "
      "about 2%."),
    q("Gravitation", "EASY",
      "The escape velocity from the earth's surface is independent of",
      ["the mass of the projected body", "the mass of the earth",
       "the radius of the earth", "the surface value of g"], 0,
      "v_e = sqrt(2GM/R) = sqrt(2gR); it does not contain the mass of the "
      "projected body."),
    q("Gravitation", "HARD",
      "The period of a satellite revolving very close to the earth's surface is "
      "approximately",
      ["84.6 minutes", "24 hours", "12 hours", "60 minutes"], 0,
      "T = 2*pi*sqrt(R/g) = 2*pi*sqrt(6.4e6/9.8) approximately 5078 s, i.e. about "
      "84.6 minutes."),

    # --- Mechanical Properties of Solids / Fluids -------------------------
    q("Mechanical Properties of Solids", "EASY",
      "The SI unit of Young's modulus of elasticity is",
      ["N m^-2", "N m", "N m^2", "N m^-1"], 0,
      "Young's modulus = stress/strain; strain is dimensionless, so the unit is "
      "that of stress, N m^-2 (pascal)."),
    q("Mechanical Properties of Fluids", "EASY",
      "Bernoulli's theorem for the steady flow of an ideal fluid is a "
      "consequence of the conservation of",
      ["energy", "mass", "momentum", "charge"], 0,
      "Bernoulli's equation is a statement of energy conservation per unit "
      "volume for a flowing ideal fluid."),
    q("Mechanical Properties of Fluids", "HARD",
      "Two raindrops have radii in the ratio 1:2. Their terminal velocities in "
      "air are in the ratio",
      ["1:4", "1:2", "1:8", "2:1"], 0,
      "Terminal velocity is proportional to r^2, so the ratio is 1^2:2^2 = 1:4."),

    # --- Thermal Properties and Thermodynamics ----------------------------
    q("Thermal Properties of Matter", "EASY",
      "When a rod of length L is heated through a temperature rise dT, its "
      "change in length is (alpha = coefficient of linear expansion)",
      ["L*alpha*dT", "L*alpha/dT", "L*dT/alpha", "L*alpha*dT^2"], 0,
      "Linear expansion: dL = L*alpha*dT."),
    q("Thermodynamics", "MEDIUM",
      "In an adiabatic process",
      ["no heat is exchanged with the surroundings",
       "the temperature remains constant",
       "the pressure remains constant",
       "the volume remains constant"], 0,
      "Adiabatic means dQ = 0; no heat enters or leaves the system."),
    q("Thermodynamics", "HARD",
      "A Carnot engine works between a source at 500 K and a sink at 300 K. Its "
      "efficiency is",
      ["40%", "60%", "20%", "80%"], 0,
      "Efficiency = 1 - T2/T1 = 1 - 300/500 = 0.40, i.e. 40%."),
    q("Thermodynamics", "EASY",
      "According to the first law of thermodynamics, the heat dQ supplied to a "
      "system equals",
      ["dU + dW", "dU - dW", "dW - dU", "dU/dW"], 0,
      "dQ = dU + dW, where dU is the change in internal energy and dW the work "
      "done by the system."),

    # --- Kinetic Theory ----------------------------------------------------
    q("Kinetic Theory of Gases", "EASY",
      "At a given temperature, the average translational kinetic energy of the "
      "molecules of a gas is",
      ["the same for all gases", "greater for heavier gases",
       "greater for lighter gases", "zero"], 0,
      "Average kinetic energy = (3/2)kT, which depends only on temperature, not "
      "on the nature of the gas."),
    q("Kinetic Theory of Gases", "HARD",
      "At the same temperature, the ratio of the rms speeds of hydrogen (M = 2) "
      "and oxygen (M = 32) molecules is",
      ["4:1", "1:4", "2:1", "1:2"], 0,
      "v_rms is proportional to 1/sqrt(M), so v_H2/v_O2 = sqrt(32/2) = 4."),

    # --- Oscillations and Waves -------------------------------------------
    q("Oscillations", "MEDIUM",
      "A simple pendulum is taken inside a lift falling freely. Its time period",
      ["becomes infinite", "becomes zero", "remains unchanged",
       "is halved"], 0,
      "In free fall the effective g is zero, so T = 2*pi*sqrt(L/g_eff) tends to "
      "infinity; the pendulum does not oscillate."),
    q("Waves", "EASY",
      "The speed of sound in air at constant pressure",
      ["increases with a rise in temperature",
       "decreases with a rise in temperature",
       "is independent of temperature",
       "is independent of humidity"], 0,
      "For a gas v is proportional to sqrt(T), so the speed rises with "
      "temperature."),
    q("Waves", "HARD",
      "A source of sound approaches a stationary observer. The apparent "
      "frequency heard by the observer",
      ["increases", "decreases", "remains the same",
       "first increases then decreases"], 0,
      "By the Doppler effect for an approaching source, f' = f v/(v - v_s) > f."),

    # --- Electrostatics ----------------------------------------------------
    q("Electrostatics", "EASY",
      "The electrostatic force between two point charges is F. If the distance "
      "between them is doubled, the force becomes",
      ["F/4", "F/2", "2F", "4F"], 0,
      "Coulomb's law gives F proportional to 1/r^2; doubling r makes the force "
      "one-fourth."),
    q("Electrostatics", "MEDIUM",
      "A charge Q is uniformly distributed over a spherical shell of radius R. "
      "The electric potential at the centre of the shell is",
      ["kQ/R", "zero", "kQ/R^2", "2kQ/R"], 0,
      "The potential is constant everywhere inside a uniformly charged shell "
      "and equals kQ/R."),
    q("Electrostatics", "MEDIUM",
      "The work done in moving a charge between two points on an equipotential "
      "surface is",
      ["zero", "maximum", "negative", "infinite"], 0,
      "The potential difference between any two points on an equipotential "
      "surface is zero, so W = q*dV = 0."),

    # --- Current Electricity ----------------------------------------------
    q("Current Electricity", "MEDIUM",
      "A wire of resistance R is stretched to double its length at constant "
      "volume. Its new resistance is",
      ["4R", "2R", "R/2", "4R/1"], 0,
      "R = rho*L/A and volume AL is constant, so R is proportional to L^2; "
      "doubling L makes the resistance 4R."),
    q("Current Electricity", "MEDIUM",
      "A Wheatstone bridge is balanced. If the cell and the galvanometer are "
      "interchanged, the bridge",
      ["remains balanced", "becomes unbalanced",
       "shows a large current in the galvanometer", "stops conducting"], 0,
      "The bridge network is symmetric under the interchange of the source and "
      "the detector, so it stays balanced."),

    # --- Moving Charges and Magnetism -------------------------------------
    q("Moving Charges and Magnetism", "EASY",
      "A charged particle moving through a magnetic field experiences no "
      "magnetic force when its velocity is",
      ["parallel or antiparallel to the field", "perpendicular to the field",
       "at 45 degrees to the field", "at 60 degrees to the field"], 0,
      "F = qvB*sin(theta); when theta = 0 or 180 degrees, sin(theta) = 0 and the "
      "force vanishes."),
    q("Moving Charges and Magnetism", "HARD",
      "In a cyclotron, the frequency of the alternating voltage applied to the "
      "dees",
      ["is independent of the speed of the particle",
       "increases as the particle speeds up",
       "decreases as the particle speeds up",
       "is independent of the magnetic field"], 0,
      "The cyclotron frequency is f = qB/(2*pi*m), independent of the particle's "
      "speed (non-relativistic)."),

    # --- Magnetism and Matter ---------------------------------------------
    q("Magnetism and Matter", "EASY",
      "Diamagnetic substances are",
      ["weakly repelled by a strong magnet", "strongly attracted by a magnet",
       "permanently magnetised", "weakly attracted by a magnet"], 0,
      "Diamagnetic materials have a small negative susceptibility and are "
      "weakly repelled by magnets."),

    # --- Electromagnetic Induction and AC ---------------------------------
    q("Electromagnetic Induction", "EASY",
      "Lenz's law is a consequence of the law of conservation of",
      ["energy", "charge", "momentum", "mass"], 0,
      "The induced current opposes the change producing it; otherwise energy "
      "could be created from nothing."),
    q("Alternating Current", "HARD",
      "In a series LCR circuit at resonance",
      ["the impedance is minimum and the power factor is unity",
       "the impedance is maximum and the current is minimum",
       "the current leads the applied voltage",
       "the current lags behind the applied voltage"], 0,
      "At resonance X_L = X_C, so Z = R (minimum), the current is maximum and the "
      "power factor cos(phi) = 1."),

    # --- Electromagnetic Waves --------------------------------------------
    q("Electromagnetic Waves", "EASY",
      "Electromagnetic waves are",
      ["transverse waves in which E, B and the direction of propagation are "
       "mutually perpendicular",
       "longitudinal waves",
       "mechanical waves requiring a medium",
       "stationary waves"], 0,
      "In an electromagnetic wave the electric and magnetic fields oscillate "
      "perpendicular to each other and to the direction of propagation."),

    # --- Optics ------------------------------------------------------------
    q("Ray Optics", "HARD",
      "The critical angle for a medium of refractive index n surrounded by air "
      "is given by",
      ["sin^-1(1/n)", "sin^-1(n)", "cos^-1(1/n)", "tan^-1(n)"], 0,
      "At the critical angle, n*sin(C) = 1, so sin(C) = 1/n."),
    q("Wave Optics", "MEDIUM",
      "In Young's double-slit experiment, the fringe width is given by",
      ["lambda*D/d", "lambda*d/D", "lambda*D^2/d", "lambda/(d*D)"], 0,
      "Fringe width = lambda*D/d, where D is the slit-to-screen distance and d "
      "the separation between the slits."),

    # --- Dual Nature, Atoms, Nuclei, Semiconductors -----------------------
    q("Dual Nature of Radiation and Matter", "MEDIUM",
      "In the photoelectric effect, the stopping potential depends on",
      ["the frequency of the incident light and the nature of the metal",
       "the intensity of the incident light only",
       "the intensity of light and the nature of the metal",
       "the area of the metal surface"], 0,
      "Einstein's equation eV0 = h*nu - phi shows that the stopping potential "
      "depends on the frequency and the work function of the metal, not on "
      "intensity."),
    q("Dual Nature of Radiation and Matter", "HARD",
      "An electron is accelerated through a potential difference V. Its de "
      "Broglie wavelength is proportional to",
      ["1/sqrt(V)", "V", "sqrt(V)", "1/V"], 0,
      "lambda = h/sqrt(2*m*e*V), so lambda is proportional to 1/sqrt(V)."),
    q("Atoms", "MEDIUM",
      "In the Bohr model of the hydrogen atom, the radius of the nth orbit is "
      "proportional to",
      ["n^2", "n", "1/n", "1/n^2"], 0,
      "r_n = n^2 * a0, where a0 is the Bohr radius."),
    q("Nuclei", "MEDIUM",
      "The binding energy per nucleon is maximum for nuclei with mass number "
      "close to",
      ["56", "4", "238", "2"], 0,
      "Binding energy per nucleon peaks near A = 56 (the iron region), making "
      "these medium-mass nuclei the most stable."),
    q("Semiconductor Electronics", "MEDIUM",
      "When a p-n junction diode is forward biased",
      ["the depletion layer becomes narrower and the diode conducts",
       "the depletion layer becomes wider and the diode does not conduct",
       "no current flows through the junction",
       "the width of the depletion layer stays unchanged"], 0,
      "Forward bias lowers the barrier potential and narrows the depletion "
      "layer, allowing a large current to flow."),
]
