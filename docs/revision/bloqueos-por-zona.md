# Bloqueos por zona de lesión

> **Pendiente de revisión por el usuario.**

Este documento se genera con `python scripts/generar_revision_bloqueos.py` a partir de las
reglas de `app/safety/reglas.py` y del catálogo real (`data/catalogo/exercises.json`,
free-exercise-db, 876 ejercicios). No se edita a mano: si cambian las reglas
o el catálogo, se vuelve a generar.

Las reglas son deterministas y conservadoras (ante la duda, se bloquea). Un ejercicio queda
bloqueado para una zona si cumple **cualquiera** de estos motivos:

- **músculo**: alguno de sus músculos primario o secundarios está en la regla de la zona.
- **patrón**: el patrón aparece en el id o en el nombre, sin distinguir mayúsculas ni
  separadores (`upright row` bloquea `Upright_Row` y `Upright-Row`).
- **id extra**: el id está en la lista explícita de la zona.

Solo las lesiones con `activa=True` aplican, y una zona activa sin regla bloquea todo el
proceso (falla cerrado). Por favor, revisa sobre todo dos cosas: ejercicios de riesgo que
**no** aparezcan aquí (falsos negativos) y bloqueos que te parezcan excesivos.

## Resumen

| Zona | Bloqueados | Permitidos |
|---|---:|---:|
| `hombro_derecho` | 612 | 264 |
| `hombro_izquierdo` | 612 | 264 |
| `rodilla_derecha` | 406 | 470 |
| `rodilla_izquierda` | 406 | 470 |
| `zona_lumbar` | 649 | 227 |

## `hombro_derecho` (612 bloqueados)

- Músculos: chest, lats, middle back, shoulders, traps
- Patrones: `overhead`, `military`, `shoulder press`, `push press`, `arnold`, `upright row`, `behind the neck`, `behind neck`, `behind the head`, `behind the back`, `dip`, `handstand`, `snatch`, `jerk`, `clean`, `thruster`, `squat`, `good morning`, `barbell lunge`, `barbell walking lunge`, `barbell step`, `barbell side`, `deadlift`, `rack pull`, `farmer`, `rickshaw`, `yoke`, `pull up`, `pullup`, `chin up`, `chinup`, `chins`, `grip chin`, `gorilla chin`, `muscle up`, `pulldown`, `pullover`, `hang`, `row`, `raise`, `bench press`, `floor press`, `chest press`, `push up`, `pushup`, `body up`, `body tricep`, `triceps extension`, `tricep extension`, `triceps press`, `tricep press`, `skull`, `kickback`, `fly`, `flye`, `crossover`, `iron cross`, `crucifix`, `rotation`, `windmill`, `get up`, `getup`, `halo`, `throw`, `slam`, `swing`, `pike`, `plank`, `crawl`, `rope`, `log lift`, `atlas stone`, `renegade`, `london bridge`, `sled`, `jammer`, `landmine`, `incline dumbbell curl`, `incline hammer`, `incline inner`, `drag curl`, `high cable curl`, `high pulley`, `against wall`, `triceps stretch`, `tricep side stretch`, `biceps stretch`, `around the world`, `circles`, `chest push`, `chest pass`, `medicine ball`, `neck press`, `svend`, `power partials`, `rack delivery`, `inchworm`, `wind sprint`, `judo flip`, `chain handle`
- Ids extra: (ninguno)

| Id | Nombre | Músculo primario | Motivo |
|---|---|---|---|
| `Ab_Roller` | Ab Roller | abdominals | músculo: shoulders |
| `Advanced_Kettlebell_Windmill` | Advanced Kettlebell Windmill | abdominals | músculo: shoulders; patrón: windmill |
| `Alternate_Incline_Dumbbell_Curl` | Alternate Incline Dumbbell Curl | biceps | patrón: incline dumbbell curl |
| `Alternating_Cable_Shoulder_Press` | Alternating Cable Shoulder Press | shoulders | músculo: shoulders; patrón: shoulder press |
| `Alternating_Deltoid_Raise` | Alternating Deltoid Raise | shoulders | músculo: shoulders; patrón: raise |
| `Alternating_Floor_Press` | Alternating Floor Press | chest | músculo: chest; músculo: shoulders; patrón: floor press |
| `Alternating_Hang_Clean` | Alternating Hang Clean | hamstrings | músculo: traps; patrón: clean; patrón: hang |
| `Alternating_Kettlebell_Press` | Alternating Kettlebell Press | shoulders | músculo: shoulders |
| `Alternating_Kettlebell_Row` | Alternating Kettlebell Row | middle back | músculo: middle back; músculo: lats; patrón: row |
| `Alternating_Renegade_Row` | Alternating Renegade Row | middle back | músculo: middle back; músculo: chest; músculo: lats; patrón: row; patrón: renegade |
| `Ankle_Circles` | Ankle Circles | calves | patrón: circles |
| `Anti-Gravity_Press` | Anti-Gravity Press | shoulders | músculo: shoulders; músculo: middle back; músculo: traps |
| `Arm_Circles` | Arm Circles | shoulders | músculo: shoulders; músculo: traps; patrón: circles |
| `Arnold_Dumbbell_Press` | Arnold Dumbbell Press | shoulders | músculo: shoulders; patrón: arnold |
| `Around_The_Worlds` | Around The Worlds | chest | músculo: chest; músculo: shoulders; patrón: around the world |
| `Atlas_Stone_Trainer` | Atlas Stone Trainer | lower back | patrón: atlas stone |
| `Atlas_Stones` | Atlas Stones | lower back | músculo: middle back; músculo: traps; patrón: atlas stone |
| `Axle_Deadlift` | Axle Deadlift | lower back | músculo: middle back; músculo: traps; patrón: deadlift |
| `Back_Flyes_-_With_Bands` | Back Flyes - With Bands | shoulders | músculo: shoulders; músculo: middle back; patrón: fly; patrón: flye |
| `Backward_Medicine_Ball_Throw` | Backward Medicine Ball Throw | shoulders | músculo: shoulders; patrón: row; patrón: throw; patrón: medicine ball |
| `Band_Assisted_Pull-Up` | Band Assisted Pull-Up | lats | músculo: lats; músculo: middle back; patrón: pull up; patrón: pullup |
| `Band_Good_Morning` | Band Good Morning | hamstrings | patrón: good morning |
| `Band_Good_Morning_Pull_Through` | Band Good Morning (Pull Through) | hamstrings | patrón: good morning |
| `Band_Pull_Apart` | Band Pull Apart | shoulders | músculo: shoulders; músculo: middle back; músculo: traps |
| `Band_Skull_Crusher` | Band Skull Crusher | triceps | patrón: skull |
| `Barbell_Ab_Rollout` | Barbell Ab Rollout | abdominals | músculo: shoulders |
| `Barbell_Ab_Rollout_-_On_Knees` | Barbell Ab Rollout - On Knees | abdominals | músculo: shoulders |
| `Barbell_Bench_Press_-_Medium_Grip` | Barbell Bench Press - Medium Grip | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Barbell_Deadlift` | Barbell Deadlift | lower back | músculo: lats; músculo: middle back; músculo: traps; patrón: deadlift |
| `Barbell_Full_Squat` | Barbell Full Squat | quadriceps | patrón: squat |
| `Barbell_Guillotine_Bench_Press` | Barbell Guillotine Bench Press | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Barbell_Hack_Squat` | Barbell Hack Squat | quadriceps | patrón: squat |
| `Barbell_Incline_Bench_Press_-_Medium_Grip` | Barbell Incline Bench Press - Medium Grip | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Barbell_Incline_Shoulder_Raise` | Barbell Incline Shoulder Raise | shoulders | músculo: shoulders; músculo: chest; patrón: raise |
| `Barbell_Lunge` | Barbell Lunge | quadriceps | patrón: barbell lunge |
| `Barbell_Rear_Delt_Row` | Barbell Rear Delt Row | shoulders | músculo: shoulders; músculo: lats; músculo: middle back; patrón: row |
| `Barbell_Rollout_from_Bench` | Barbell Rollout from Bench | abdominals | músculo: lats; músculo: shoulders |
| `Barbell_Seated_Calf_Raise` | Barbell Seated Calf Raise | calves | patrón: raise |
| `Barbell_Shoulder_Press` | Barbell Shoulder Press | shoulders | músculo: shoulders; músculo: chest; patrón: shoulder press |
| `Barbell_Shrug` | Barbell Shrug | traps | músculo: traps |
| `Barbell_Shrug_Behind_The_Back` | Barbell Shrug Behind The Back | traps | músculo: traps; músculo: middle back; patrón: behind the back |
| `Barbell_Side_Bend` | Barbell Side Bend | abdominals | patrón: barbell side |
| `Barbell_Side_Split_Squat` | Barbell Side Split Squat | quadriceps | patrón: squat; patrón: barbell side |
| `Barbell_Squat` | Barbell Squat | quadriceps | patrón: squat |
| `Barbell_Squat_To_A_Bench` | Barbell Squat To A Bench | quadriceps | patrón: squat |
| `Barbell_Step_Ups` | Barbell Step Ups | quadriceps | patrón: barbell step |
| `Barbell_Walking_Lunge` | Barbell Walking Lunge | quadriceps | patrón: barbell walking lunge |
| `Battling_Ropes` | Battling Ropes | shoulders | músculo: shoulders; músculo: chest; patrón: rope |
| `Bear_Crawl_Sled_Drags` | Bear Crawl Sled Drags | quadriceps | patrón: crawl; patrón: sled |
| `Behind_Head_Chest_Stretch` | Behind Head Chest Stretch | chest | músculo: chest; músculo: shoulders |
| `Bench_Dips` | Bench Dips | triceps | músculo: chest; músculo: shoulders; patrón: dip |
| `Bench_Press_-_Powerlifting` | Bench Press - Powerlifting | triceps | músculo: chest; músculo: lats; músculo: shoulders; patrón: bench press |
| `Bench_Press_-_With_Bands` | Bench Press - With Bands | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Bench_Press_with_Chains` | Bench Press with Chains | triceps | músculo: chest; músculo: lats; músculo: shoulders; patrón: bench press |
| `Bent-Arm_Barbell_Pullover` | Bent-Arm Barbell Pullover | lats | músculo: lats; músculo: chest; músculo: shoulders; patrón: pullover |
| `Bent-Arm_Dumbbell_Pullover` | Bent-Arm Dumbbell Pullover | chest | músculo: chest; músculo: lats; músculo: shoulders; patrón: pullover |
| `Bent-Knee_Hip_Raise` | Bent-Knee Hip Raise | abdominals | patrón: raise |
| `Bent_Over_Barbell_Row` | Bent Over Barbell Row | middle back | músculo: middle back; músculo: lats; músculo: shoulders; patrón: row |
| `Bent_Over_Dumbbell_Rear_Delt_Raise_With_Head_On_Bench` | Bent Over Dumbbell Rear Delt Raise With Head On Bench | shoulders | músculo: shoulders; patrón: raise |
| `Bent_Over_Low-Pulley_Side_Lateral` | Bent Over Low-Pulley Side Lateral | shoulders | músculo: shoulders; músculo: middle back; músculo: traps |
| `Bent_Over_One-Arm_Long_Bar_Row` | Bent Over One-Arm Long Bar Row | middle back | músculo: middle back; músculo: lats; músculo: traps; patrón: row |
| `Bent_Over_Two-Arm_Long_Bar_Row` | Bent Over Two-Arm Long Bar Row | middle back | músculo: middle back; músculo: lats; patrón: row |
| `Bent_Over_Two-Dumbbell_Row` | Bent Over Two-Dumbbell Row | middle back | músculo: middle back; músculo: lats; músculo: shoulders; patrón: row |
| `Bent_Over_Two-Dumbbell_Row_With_Palms_In` | Bent Over Two-Dumbbell Row With Palms In | middle back | músculo: middle back; músculo: lats; patrón: row |
| `Bent_Press` | Bent Press | abdominals | músculo: shoulders |
| `Board_Press` | Board Press | triceps | músculo: chest; músculo: lats; músculo: shoulders |
| `Body-Up` | Body-Up | triceps | patrón: body up |
| `Body_Tricep_Press` | Body Tricep Press | triceps | patrón: body tricep; patrón: tricep press |
| `Bodyweight_Flyes` | Bodyweight Flyes | chest | músculo: chest; músculo: shoulders; patrón: fly; patrón: flye |
| `Bodyweight_Mid_Row` | Bodyweight Mid Row | middle back | músculo: middle back; músculo: lats; patrón: row |
| `Bodyweight_Squat` | Bodyweight Squat | quadriceps | patrón: squat |
| `Bottoms-Up_Clean_From_The_Hang_Position` | Bottoms-Up Clean From The Hang Position | forearms | músculo: shoulders; patrón: clean; patrón: hang |
| `Box_Squat` | Box Squat | quadriceps | patrón: squat |
| `Box_Squat_with_Bands` | Box Squat with Bands | quadriceps | patrón: squat |
| `Box_Squat_with_Chains` | Box Squat with Chains | quadriceps | patrón: squat |
| `Bradford_Rocky_Presses` | Bradford/Rocky Presses | shoulders | músculo: shoulders |
| `Butterfly` | Butterfly | chest | músculo: chest; patrón: fly |
| `Cable_Chest_Press` | Cable Chest Press | chest | músculo: chest; músculo: shoulders; patrón: chest press |
| `Cable_Crossover` | Cable Crossover | chest | músculo: chest; músculo: shoulders; patrón: crossover |
| `Cable_Deadlifts` | Cable Deadlifts | quadriceps | patrón: deadlift |
| `Cable_Hammer_Curls_-_Rope_Attachment` | Cable Hammer Curls - Rope Attachment | biceps | patrón: rope |
| `Cable_Incline_Pushdown` | Cable Incline Pushdown | lats | músculo: lats |
| `Cable_Incline_Triceps_Extension` | Cable Incline Triceps Extension | triceps | patrón: triceps extension |
| `Cable_Internal_Rotation` | Cable Internal Rotation | shoulders | músculo: shoulders; patrón: rotation |
| `Cable_Iron_Cross` | Cable Iron Cross | chest | músculo: chest; patrón: iron cross |
| `Cable_Judo_Flip` | Cable Judo Flip | abdominals | patrón: judo flip |
| `Cable_Lying_Triceps_Extension` | Cable Lying Triceps Extension | triceps | patrón: triceps extension |
| `Cable_One_Arm_Tricep_Extension` | Cable One Arm Tricep Extension | triceps | patrón: tricep extension |
| `Cable_Rear_Delt_Fly` | Cable Rear Delt Fly | shoulders | músculo: shoulders; patrón: fly |
| `Cable_Rope_Overhead_Triceps_Extension` | Cable Rope Overhead Triceps Extension | triceps | patrón: overhead; patrón: triceps extension; patrón: rope |
| `Cable_Rope_Rear-Delt_Rows` | Cable Rope Rear-Delt Rows | shoulders | músculo: shoulders; músculo: middle back; patrón: row; patrón: rope |
| `Cable_Seated_Lateral_Raise` | Cable Seated Lateral Raise | shoulders | músculo: shoulders; músculo: middle back; músculo: traps; patrón: raise |
| `Cable_Shoulder_Press` | Cable Shoulder Press | shoulders | músculo: shoulders; patrón: shoulder press |
| `Cable_Shrugs` | Cable Shrugs | traps | músculo: traps |
| `Calf-Machine_Shoulder_Shrug` | Calf-Machine Shoulder Shrug | traps | músculo: traps |
| `Calf_Raise_On_A_Dumbbell` | Calf Raise On A Dumbbell | calves | patrón: raise |
| `Calf_Raises_-_With_Bands` | Calf Raises - With Bands | calves | patrón: raise |
| `Calf_Stretch_Elbows_Against_Wall` | Calf Stretch Elbows Against Wall | calves | patrón: against wall |
| `Calf_Stretch_Hands_Against_Wall` | Calf Stretch Hands Against Wall | calves | patrón: against wall |
| `Car_Deadlift` | Car Deadlift | quadriceps | músculo: traps; patrón: deadlift |
| `Car_Drivers` | Car Drivers | shoulders | músculo: shoulders |
| `Cat_Stretch` | Cat Stretch | lower back | músculo: middle back; músculo: traps |
| `Catch_and_Overhead_Throw` | Catch and Overhead Throw | lats | músculo: lats; músculo: chest; músculo: shoulders; patrón: overhead; patrón: row; patrón: throw |
| `Chain_Handle_Extension` | Chain Handle Extension | triceps | patrón: chain handle |
| `Chain_Press` | Chain Press | chest | músculo: chest; músculo: shoulders |
| `Chair_Lower_Back_Stretch` | Chair Lower Back Stretch | lats | músculo: lats |
| `Chair_Squat` | Chair Squat | quadriceps | patrón: squat |
| `Chair_Upper_Body_Stretch` | Chair Upper Body Stretch | shoulders | músculo: shoulders; músculo: chest |
| `Chest_And_Front_Of_Shoulder_Stretch` | Chest And Front Of Shoulder Stretch | chest | músculo: chest; músculo: shoulders |
| `Chest_Push_from_3_point_stance` | Chest Push from 3 point stance | chest | músculo: chest; músculo: shoulders; patrón: chest push |
| `Chest_Push_multiple_response` | Chest Push (multiple response) | chest | músculo: chest; músculo: shoulders; patrón: chest push |
| `Chest_Push_single_response` | Chest Push (single response) | chest | músculo: chest; músculo: shoulders; patrón: chest push |
| `Chest_Push_with_Run_Release` | Chest Push with Run Release | chest | músculo: chest; músculo: shoulders; patrón: chest push |
| `Chest_Stretch_on_Stability_Ball` | Chest Stretch on Stability Ball | chest | músculo: chest |
| `Childs_Pose` | Child's Pose | lower back | músculo: middle back |
| `Chin-Up` | Chin-Up | lats | músculo: lats; músculo: middle back; patrón: chin up; patrón: chinup |
| `Chin_To_Chest_Stretch` | Chin To Chest Stretch | neck | músculo: traps |
| `Circus_Bell` | Circus Bell | shoulders | músculo: shoulders; músculo: traps |
| `Clean` | Clean | hamstrings | músculo: shoulders; músculo: traps; patrón: clean |
| `Clean_Deadlift` | Clean Deadlift | hamstrings | músculo: middle back; músculo: traps; patrón: clean; patrón: deadlift |
| `Clean_Pull` | Clean Pull | quadriceps | músculo: traps; patrón: clean |
| `Clean_Shrug` | Clean Shrug | traps | músculo: traps; músculo: shoulders; patrón: clean |
| `Clean_and_Jerk` | Clean and Jerk | shoulders | músculo: shoulders; músculo: traps; patrón: jerk; patrón: clean |
| `Clean_and_Press` | Clean and Press | shoulders | músculo: shoulders; músculo: middle back; músculo: traps; patrón: clean |
| `Clean_from_Blocks` | Clean from Blocks | quadriceps | músculo: shoulders; músculo: traps; patrón: clean |
| `Clock_Push-Up` | Clock Push-Up | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Close-Grip_Barbell_Bench_Press` | Close-Grip Barbell Bench Press | triceps | músculo: chest; músculo: shoulders; patrón: bench press |
| `Close-Grip_Dumbbell_Press` | Close-Grip Dumbbell Press | triceps | músculo: chest; músculo: shoulders |
| `Close-Grip_EZ-Bar_Press` | Close-Grip EZ-Bar Press | triceps | músculo: chest; músculo: shoulders |
| `Close-Grip_Front_Lat_Pulldown` | Close-Grip Front Lat Pulldown | lats | músculo: lats; músculo: middle back; músculo: shoulders; patrón: pulldown |
| `Close-Grip_Push-Up_off_of_a_Dumbbell` | Close-Grip Push-Up off of a Dumbbell | triceps | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Conans_Wheel` | Conan's Wheel | quadriceps | músculo: shoulders; músculo: traps |
| `Cross_Over_-_With_Bands` | Cross Over - With Bands | chest | músculo: chest; músculo: shoulders; patrón: crossover |
| `Crossover_Reverse_Lunge` | Crossover Reverse Lunge | lower back | patrón: crossover |
| `Crucifix` | Crucifix | shoulders | músculo: shoulders; patrón: crucifix |
| `Crunch_-_Hands_Overhead` | Crunch - Hands Overhead | abdominals | patrón: overhead |
| `Cuban_Press` | Cuban Press | shoulders | músculo: shoulders; músculo: traps |
| `Deadlift_with_Bands` | Deadlift with Bands | lower back | músculo: middle back; músculo: traps; patrón: deadlift |
| `Deadlift_with_Chains` | Deadlift with Chains | lower back | músculo: middle back; músculo: traps; patrón: deadlift |
| `Decline_Barbell_Bench_Press` | Decline Barbell Bench Press | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Decline_Close-Grip_Bench_To_Skull_Crusher` | Decline Close-Grip Bench To Skull Crusher | triceps | músculo: chest; músculo: shoulders; patrón: skull |
| `Decline_Dumbbell_Bench_Press` | Decline Dumbbell Bench Press | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Decline_Dumbbell_Flyes` | Decline Dumbbell Flyes | chest | músculo: chest; patrón: fly; patrón: flye |
| `Decline_Dumbbell_Triceps_Extension` | Decline Dumbbell Triceps Extension | triceps | patrón: triceps extension |
| `Decline_EZ_Bar_Triceps_Extension` | Decline EZ Bar Triceps Extension | triceps | patrón: triceps extension |
| `Decline_Push-Up` | Decline Push-Up | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Decline_Smith_Press` | Decline Smith Press | chest | músculo: chest; músculo: shoulders |
| `Deficit_Deadlift` | Deficit Deadlift | lower back | músculo: middle back; músculo: traps; patrón: deadlift |
| `Dip_Machine` | Dip Machine | triceps | músculo: chest; músculo: shoulders; patrón: dip |
| `Dips_-_Chest_Version` | Dips - Chest Version | chest | músculo: chest; músculo: shoulders; patrón: dip |
| `Dips_-_Triceps_Version` | Dips - Triceps Version | triceps | músculo: chest; músculo: shoulders; patrón: dip |
| `Donkey_Calf_Raises` | Donkey Calf Raises | calves | patrón: raise |
| `Double_Kettlebell_Alternating_Hang_Clean` | Double Kettlebell Alternating Hang Clean | hamstrings | músculo: traps; patrón: clean; patrón: hang |
| `Double_Kettlebell_Jerk` | Double Kettlebell Jerk | shoulders | músculo: shoulders; patrón: jerk |
| `Double_Kettlebell_Push_Press` | Double Kettlebell Push Press | shoulders | músculo: shoulders; patrón: push press |
| `Double_Kettlebell_Snatch` | Double Kettlebell Snatch | shoulders | músculo: shoulders; patrón: snatch |
| `Double_Kettlebell_Windmill` | Double Kettlebell Windmill | abdominals | músculo: shoulders; patrón: windmill |
| `Drag_Curl` | Drag Curl | biceps | patrón: drag curl |
| `Drop_Push` | Drop Push | chest | músculo: chest; músculo: shoulders |
| `Dumbbell_Bench_Press` | Dumbbell Bench Press | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Dumbbell_Bench_Press_with_Neutral_Grip` | Dumbbell Bench Press with Neutral Grip | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Dumbbell_Clean` | Dumbbell Clean | hamstrings | músculo: shoulders; músculo: traps; patrón: clean |
| `Dumbbell_Floor_Press` | Dumbbell Floor Press | triceps | músculo: chest; músculo: shoulders; patrón: floor press |
| `Dumbbell_Flyes` | Dumbbell Flyes | chest | músculo: chest; patrón: fly; patrón: flye |
| `Dumbbell_Incline_Row` | Dumbbell Incline Row | middle back | músculo: middle back; músculo: lats; músculo: shoulders; patrón: row |
| `Dumbbell_Incline_Shoulder_Raise` | Dumbbell Incline Shoulder Raise | shoulders | músculo: shoulders; patrón: raise |
| `Dumbbell_Lying_One-Arm_Rear_Lateral_Raise` | Dumbbell Lying One-Arm Rear Lateral Raise | shoulders | músculo: shoulders; músculo: middle back; patrón: raise |
| `Dumbbell_Lying_Rear_Lateral_Raise` | Dumbbell Lying Rear Lateral Raise | shoulders | músculo: shoulders; patrón: raise |
| `Dumbbell_One-Arm_Shoulder_Press` | Dumbbell One-Arm Shoulder Press | shoulders | músculo: shoulders; patrón: shoulder press |
| `Dumbbell_One-Arm_Triceps_Extension` | Dumbbell One-Arm Triceps Extension | triceps | patrón: triceps extension |
| `Dumbbell_One-Arm_Upright_Row` | Dumbbell One-Arm Upright Row | shoulders | músculo: shoulders; músculo: traps; patrón: upright row; patrón: row |
| `Dumbbell_Raise` | Dumbbell Raise | shoulders | músculo: shoulders; patrón: raise |
| `Dumbbell_Scaption` | Dumbbell Scaption | shoulders | músculo: shoulders; músculo: traps |
| `Dumbbell_Seated_One-Leg_Calf_Raise` | Dumbbell Seated One-Leg Calf Raise | calves | patrón: raise |
| `Dumbbell_Shoulder_Press` | Dumbbell Shoulder Press | shoulders | músculo: shoulders; patrón: shoulder press |
| `Dumbbell_Shrug` | Dumbbell Shrug | traps | músculo: traps |
| `Dumbbell_Squat` | Dumbbell Squat | quadriceps | patrón: squat |
| `Dumbbell_Squat_To_A_Bench` | Dumbbell Squat To A Bench | quadriceps | patrón: squat |
| `Dumbbell_Tricep_Extension_-Pronated_Grip` | Dumbbell Tricep Extension -Pronated Grip | triceps | patrón: tricep extension |
| `Dynamic_Back_Stretch` | Dynamic Back Stretch | lats | músculo: lats |
| `Dynamic_Chest_Stretch` | Dynamic Chest Stretch | chest | músculo: chest; músculo: middle back |
| `EZ-Bar_Skullcrusher` | EZ-Bar Skullcrusher | triceps | patrón: skull |
| `Elbow_Circles` | Elbow Circles | shoulders | músculo: shoulders; músculo: traps; patrón: circles |
| `Elbows_Back` | Elbows Back | chest | músculo: chest; músculo: shoulders |
| `Elevated_Cable_Rows` | Elevated Cable Rows | lats | músculo: lats; músculo: middle back; músculo: traps; patrón: row |
| `Extended_Range_One-Arm_Kettlebell_Floor_Press` | Extended Range One-Arm Kettlebell Floor Press | chest | músculo: chest; músculo: shoulders; patrón: floor press |
| `External_Rotation` | External Rotation | shoulders | músculo: shoulders; patrón: rotation |
| `External_Rotation_with_Band` | External Rotation with Band | shoulders | músculo: shoulders; patrón: rotation |
| `External_Rotation_with_Cable` | External Rotation with Cable | shoulders | músculo: shoulders; patrón: rotation |
| `Face_Pull` | Face Pull | shoulders | músculo: shoulders; músculo: middle back |
| `Farmers_Walk` | Farmer's Walk | forearms | músculo: traps; patrón: farmer |
| `Flat_Bench_Cable_Flyes` | Flat Bench Cable Flyes | chest | músculo: chest; patrón: fly; patrón: flye |
| `Flat_Bench_Lying_Leg_Raise` | Flat Bench Lying Leg Raise | abdominals | patrón: raise |
| `Flexor_Incline_Dumbbell_Curls` | Flexor Incline Dumbbell Curls | biceps | patrón: incline dumbbell curl |
| `Floor_Glute-Ham_Raise` | Floor Glute-Ham Raise | hamstrings | patrón: raise |
| `Floor_Press` | Floor Press | triceps | músculo: chest; músculo: shoulders; patrón: floor press |
| `Floor_Press_with_Chains` | Floor Press with Chains | triceps | músculo: chest; músculo: shoulders; patrón: floor press |
| `Forward_Drag_with_Press` | Forward Drag with Press | chest | músculo: chest; músculo: shoulders |
| `Frankenstein_Squat` | Frankenstein Squat | quadriceps | patrón: squat |
| `Freehand_Jump_Squat` | Freehand Jump Squat | quadriceps | patrón: squat |
| `Front_Barbell_Squat` | Front Barbell Squat | quadriceps | patrón: squat |
| `Front_Barbell_Squat_To_A_Bench` | Front Barbell Squat To A Bench | quadriceps | patrón: squat |
| `Front_Cable_Raise` | Front Cable Raise | shoulders | músculo: shoulders; patrón: raise |
| `Front_Dumbbell_Raise` | Front Dumbbell Raise | shoulders | músculo: shoulders; patrón: raise |
| `Front_Incline_Dumbbell_Raise` | Front Incline Dumbbell Raise | shoulders | músculo: shoulders; patrón: raise |
| `Front_Leg_Raises` | Front Leg Raises | hamstrings | patrón: raise |
| `Front_Plate_Raise` | Front Plate Raise | shoulders | músculo: shoulders; patrón: raise |
| `Front_Raise_And_Pullover` | Front Raise And Pullover | chest | músculo: chest; músculo: lats; músculo: shoulders; patrón: pullover; patrón: raise |
| `Front_Squat_Clean_Grip` | Front Squat (Clean Grip) | quadriceps | patrón: clean; patrón: squat |
| `Front_Squats_With_Two_Kettlebells` | Front Squats With Two Kettlebells | quadriceps | patrón: squat |
| `Front_Two-Dumbbell_Raise` | Front Two-Dumbbell Raise | shoulders | músculo: shoulders; patrón: raise |
| `Full_Range-Of-Motion_Lat_Pulldown` | Full Range-Of-Motion Lat Pulldown | lats | músculo: lats; músculo: middle back; músculo: shoulders; patrón: pulldown |
| `Gironda_Sternum_Chins` | Gironda Sternum Chins | lats | músculo: lats; músculo: middle back; patrón: chins |
| `Glute_Ham_Raise` | Glute Ham Raise | hamstrings | patrón: raise |
| `Glute_Kickback` | Glute Kickback | glutes | patrón: kickback |
| `Goblet_Squat` | Goblet Squat | quadriceps | músculo: shoulders; patrón: squat |
| `Good_Morning` | Good Morning | hamstrings | patrón: good morning |
| `Good_Morning_off_Pins` | Good Morning off Pins | hamstrings | patrón: good morning |
| `Gorilla_Chin_Crunch` | Gorilla Chin/Crunch | abdominals | músculo: lats; patrón: gorilla chin |
| `Hack_Squat` | Hack Squat | quadriceps | patrón: squat |
| `Hammer_Grip_Incline_DB_Bench_Press` | Hammer Grip Incline DB Bench Press | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Handstand_Push-Ups` | Handstand Push-Ups | shoulders | músculo: shoulders; patrón: handstand; patrón: push up; patrón: pushup |
| `Hang_Clean` | Hang Clean | quadriceps | músculo: shoulders; músculo: traps; patrón: clean; patrón: hang |
| `Hang_Clean_-_Below_the_Knees` | Hang Clean - Below the Knees | quadriceps | músculo: shoulders; músculo: traps; patrón: clean; patrón: hang |
| `Hang_Snatch` | Hang Snatch | hamstrings | músculo: shoulders; músculo: traps; patrón: snatch; patrón: hang |
| `Hang_Snatch_-_Below_Knees` | Hang Snatch - Below Knees | hamstrings | músculo: shoulders; músculo: traps; patrón: snatch; patrón: hang |
| `Hanging_Bar_Good_Morning` | Hanging Bar Good Morning | hamstrings | patrón: good morning; patrón: hang |
| `Hanging_Leg_Raise` | Hanging Leg Raise | abdominals | patrón: hang; patrón: raise |
| `Hanging_Pike` | Hanging Pike | abdominals | patrón: hang; patrón: pike |
| `Heaving_Snatch_Balance` | Heaving Snatch Balance | quadriceps | músculo: shoulders; patrón: snatch |
| `Heavy_Bag_Thrust` | Heavy Bag Thrust | chest | músculo: chest; músculo: shoulders |
| `High_Cable_Curls` | High Cable Curls | biceps | patrón: high cable curl |
| `Hip_Circles_prone` | Hip Circles (prone) | abductors | patrón: circles |
| `Inchworm` | Inchworm | hamstrings | patrón: inchworm |
| `Incline_Barbell_Triceps_Extension` | Incline Barbell Triceps Extension | triceps | patrón: triceps extension |
| `Incline_Bench_Pull` | Incline Bench Pull | middle back | músculo: middle back; músculo: lats; músculo: shoulders |
| `Incline_Cable_Chest_Press` | Incline Cable Chest Press | chest | músculo: chest; músculo: shoulders; patrón: chest press |
| `Incline_Cable_Flye` | Incline Cable Flye | chest | músculo: chest; músculo: shoulders; patrón: fly; patrón: flye |
| `Incline_Dumbbell_Bench_With_Palms_Facing_In` | Incline Dumbbell Bench With Palms Facing In | chest | músculo: chest; músculo: shoulders |
| `Incline_Dumbbell_Curl` | Incline Dumbbell Curl | biceps | patrón: incline dumbbell curl |
| `Incline_Dumbbell_Flyes` | Incline Dumbbell Flyes | chest | músculo: chest; músculo: shoulders; patrón: fly; patrón: flye |
| `Incline_Dumbbell_Flyes_-_With_A_Twist` | Incline Dumbbell Flyes - With A Twist | chest | músculo: chest; músculo: shoulders; patrón: fly; patrón: flye |
| `Incline_Dumbbell_Press` | Incline Dumbbell Press | chest | músculo: chest; músculo: shoulders |
| `Incline_Hammer_Curls` | Incline Hammer Curls | biceps | patrón: incline hammer |
| `Incline_Inner_Biceps_Curl` | Incline Inner Biceps Curl | biceps | patrón: incline inner |
| `Incline_Push-Up` | Incline Push-Up | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Incline_Push-Up_Close-Grip` | Incline Push-Up Close-Grip | triceps | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Incline_Push-Up_Depth_Jump` | Incline Push-Up Depth Jump | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Incline_Push-Up_Medium` | Incline Push-Up Medium | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Incline_Push-Up_Reverse_Grip` | Incline Push-Up Reverse Grip | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Incline_Push-Up_Wide` | Incline Push-Up Wide | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Internal_Rotation_with_Band` | Internal Rotation with Band | shoulders | músculo: shoulders; patrón: rotation |
| `Inverted_Row` | Inverted Row | middle back | músculo: middle back; músculo: lats; patrón: row |
| `Inverted_Row_with_Straps` | Inverted Row with Straps | middle back | músculo: middle back; músculo: lats; patrón: row |
| `Iron_Cross` | Iron Cross | shoulders | músculo: shoulders; músculo: chest; músculo: traps; patrón: iron cross |
| `Iron_Crosses_stretch` | Iron Crosses (stretch) | quadriceps | patrón: iron cross |
| `Isometric_Chest_Squeezes` | Isometric Chest Squeezes | chest | músculo: chest; músculo: shoulders |
| `Isometric_Wipers` | Isometric Wipers | chest | músculo: chest; músculo: shoulders |
| `JM_Press` | JM Press | triceps | músculo: chest; músculo: shoulders |
| `Jefferson_Squats` | Jefferson Squats | quadriceps | músculo: traps; patrón: squat |
| `Jerk_Balance` | Jerk Balance | shoulders | músculo: shoulders; patrón: jerk |
| `Jerk_Dip_Squat` | Jerk Dip Squat | quadriceps | patrón: dip; patrón: jerk; patrón: squat |
| `Keg_Load` | Keg Load | lower back | músculo: middle back; músculo: shoulders; músculo: traps |
| `Kettlebell_Arnold_Press` | Kettlebell Arnold Press | shoulders | músculo: shoulders; patrón: arnold |
| `Kettlebell_Dead_Clean` | Kettlebell Dead Clean | hamstrings | músculo: traps; patrón: clean |
| `Kettlebell_Figure_8` | Kettlebell Figure 8 | abdominals | músculo: shoulders |
| `Kettlebell_Halo` | Kettlebell Halo | shoulders | músculo: shoulders; músculo: traps; músculo: middle back; patrón: halo |
| `Kettlebell_Halo_With_Overhead_Extension` | Kettlebell Halo with Overhead Extension | shoulders | músculo: shoulders; músculo: traps; músculo: middle back; patrón: overhead; patrón: halo |
| `Kettlebell_Hang_Clean` | Kettlebell Hang Clean | hamstrings | músculo: shoulders; músculo: traps; patrón: clean; patrón: hang |
| `Kettlebell_One-Legged_Deadlift` | Kettlebell One-Legged Deadlift | hamstrings | patrón: deadlift |
| `Kettlebell_Overhead_Triceps_Extension` | Kettlebell Overhead Triceps Extension | triceps | músculo: shoulders; patrón: overhead; patrón: triceps extension |
| `Kettlebell_Pass_Between_The_Legs` | Kettlebell Pass Between The Legs | abdominals | músculo: shoulders |
| `Kettlebell_Pirate_Ships` | Kettlebell Pirate Ships | shoulders | músculo: shoulders |
| `Kettlebell_Pistol_Squat` | Kettlebell Pistol Squat | quadriceps | músculo: shoulders; patrón: squat |
| `Kettlebell_Seated_Press` | Kettlebell Seated Press | shoulders | músculo: shoulders |
| `Kettlebell_Seesaw_Press` | Kettlebell Seesaw Press | shoulders | músculo: shoulders |
| `Kettlebell_Sumo_High_Pull` | Kettlebell Sumo High Pull | traps | músculo: traps; músculo: shoulders |
| `Kettlebell_Thruster` | Kettlebell Thruster | shoulders | músculo: shoulders; patrón: thruster |
| `Kettlebell_Turkish_Get-Up_Lunge_style` | Kettlebell Turkish Get-Up (Lunge style) | shoulders | músculo: shoulders; patrón: get up; patrón: getup |
| `Kettlebell_Turkish_Get-Up_Squat_style` | Kettlebell Turkish Get-Up (Squat style) | shoulders | músculo: shoulders; patrón: squat; patrón: get up; patrón: getup |
| `Kettlebell_Windmill` | Kettlebell Windmill | abdominals | músculo: shoulders; patrón: windmill |
| `Kipping_Muscle_Up` | Kipping Muscle Up | lats | músculo: lats; músculo: middle back; músculo: shoulders; músculo: traps; patrón: muscle up |
| `Knee_Circles` | Knee Circles | calves | patrón: circles |
| `Knee_Hip_Raise_On_Parallel_Bars` | Knee/Hip Raise On Parallel Bars | abdominals | patrón: raise |
| `Kneeling_Arm_Drill` | Kneeling Arm Drill | shoulders | músculo: shoulders |
| `Kneeling_Cable_Triceps_Extension` | Kneeling Cable Triceps Extension | triceps | patrón: triceps extension |
| `Kneeling_High_Pulley_Row` | Kneeling High Pulley Row | lats | músculo: lats; músculo: middle back; patrón: row; patrón: high pulley |
| `Kneeling_Jump_Squat` | Kneeling Jump Squat | glutes | patrón: squat |
| `Kneeling_Single-Arm_High_Pulley_Row` | Kneeling Single-Arm High Pulley Row | lats | músculo: lats; músculo: middle back; patrón: row; patrón: high pulley |
| `Kneeling_Squat` | Kneeling Squat | glutes | patrón: squat |
| `Landmine_180s` | Landmine 180's | abdominals | músculo: shoulders; patrón: landmine |
| `Landmine_Linear_Jammer` | Landmine Linear Jammer | shoulders | músculo: shoulders; músculo: chest; patrón: jammer; patrón: landmine |
| `Lateral_Raise_-_With_Bands` | Lateral Raise - With Bands | shoulders | músculo: shoulders; patrón: raise |
| `Latissimus_Dorsi-SMR` | Latissimus Dorsi-SMR | lats | músculo: lats |
| `Leg-Over_Floor_Press` | Leg-Over Floor Press | chest | músculo: chest; músculo: shoulders; patrón: floor press |
| `Leverage_Chest_Press` | Leverage Chest Press | chest | músculo: chest; músculo: shoulders; patrón: chest press |
| `Leverage_Deadlift` | Leverage Deadlift | quadriceps | patrón: deadlift |
| `Leverage_Decline_Chest_Press` | Leverage Decline Chest Press | chest | músculo: chest; músculo: shoulders; patrón: chest press |
| `Leverage_High_Row` | Leverage High Row | middle back | músculo: middle back; músculo: lats; patrón: row |
| `Leverage_Incline_Chest_Press` | Leverage Incline Chest Press | chest | músculo: chest; músculo: shoulders; patrón: chest press |
| `Leverage_Iso_Row` | Leverage Iso Row | lats | músculo: lats; músculo: middle back; patrón: row |
| `Leverage_Shoulder_Press` | Leverage Shoulder Press | shoulders | músculo: shoulders; patrón: shoulder press |
| `Leverage_Shrug` | Leverage Shrug | traps | músculo: traps |
| `Log_Lift` | Log Lift | shoulders | músculo: shoulders; músculo: chest; músculo: middle back; músculo: traps; patrón: log lift |
| `London_Bridges` | London Bridges | lats | músculo: lats; músculo: middle back; patrón: london bridge |
| `Low_Cable_Crossover` | Low Cable Crossover | chest | músculo: chest; músculo: shoulders; patrón: crossover |
| `Low_Cable_Triceps_Extension` | Low Cable Triceps Extension | triceps | patrón: triceps extension |
| `Low_Pulley_Row_To_Neck` | Low Pulley Row To Neck | shoulders | músculo: shoulders; músculo: middle back; músculo: traps; patrón: row |
| `Lying_Cambered_Barbell_Row` | Lying Cambered Barbell Row | middle back | músculo: middle back; músculo: lats; músculo: traps; patrón: row |
| `Lying_Close-Grip_Bar_Curl_On_High_Pulley` | Lying Close-Grip Bar Curl On High Pulley | biceps | patrón: high pulley |
| `Lying_Close-Grip_Barbell_Triceps_Extension_Behind_The_Head` | Lying Close-Grip Barbell Triceps Extension Behind The Head | triceps | patrón: behind the head; patrón: triceps extension |
| `Lying_Close-Grip_Barbell_Triceps_Press_To_Chin` | Lying Close-Grip Barbell Triceps Press To Chin | triceps | patrón: triceps press |
| `Lying_Crossover` | Lying Crossover | abductors | patrón: crossover |
| `Lying_Dumbbell_Tricep_Extension` | Lying Dumbbell Tricep Extension | triceps | músculo: chest; músculo: shoulders; patrón: tricep extension |
| `Lying_Machine_Squat` | Lying Machine Squat | quadriceps | patrón: squat |
| `Lying_One-Arm_Lateral_Raise` | Lying One-Arm Lateral Raise | shoulders | músculo: shoulders; patrón: raise |
| `Lying_Rear_Delt_Raise` | Lying Rear Delt Raise | shoulders | músculo: shoulders; patrón: raise |
| `Lying_T-Bar_Row` | Lying T-Bar Row | middle back | músculo: middle back; músculo: lats; patrón: row |
| `Lying_Triceps_Press` | Lying Triceps Press | triceps | patrón: triceps press |
| `Machine_Bench_Press` | Machine Bench Press | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Machine_Shoulder_Military_Press` | Machine Shoulder (Military) Press | shoulders | músculo: shoulders; patrón: military |
| `Machine_Triceps_Extension` | Machine Triceps Extension | triceps | patrón: triceps extension |
| `Medicine_Ball_Chest_Pass` | Medicine Ball Chest Pass | chest | músculo: chest; músculo: shoulders; patrón: chest pass; patrón: medicine ball |
| `Medicine_Ball_Full_Twist` | Medicine Ball Full Twist | abdominals | músculo: shoulders; patrón: medicine ball |
| `Medicine_Ball_Scoop_Throw` | Medicine Ball Scoop Throw | shoulders | músculo: shoulders; patrón: row; patrón: throw; patrón: medicine ball |
| `Middle_Back_Shrug` | Middle Back Shrug | middle back | músculo: middle back |
| `Middle_Back_Stretch` | Middle Back Stretch | middle back | músculo: middle back; músculo: lats |
| `Mixed_Grip_Chin` | Mixed Grip Chin | middle back | músculo: middle back; músculo: lats; patrón: grip chin |
| `Mountain_Climbers` | Mountain Climbers | quadriceps | músculo: chest; músculo: shoulders |
| `Muscle_Snatch` | Muscle Snatch | hamstrings | músculo: shoulders; patrón: snatch |
| `Muscle_Up` | Muscle Up | lats | músculo: lats; músculo: middle back; músculo: shoulders; músculo: traps; patrón: muscle up |
| `Narrow_Stance_Hack_Squats` | Narrow Stance Hack Squats | quadriceps | patrón: squat; patrón: row |
| `Narrow_Stance_Leg_Press` | Narrow Stance Leg Press | quadriceps | patrón: row |
| `Narrow_Stance_Squats` | Narrow Stance Squats | quadriceps | patrón: squat; patrón: row |
| `Natural_Glute_Ham_Raise` | Natural Glute Ham Raise | hamstrings | patrón: raise |
| `Neck_Press` | Neck Press | chest | músculo: chest; músculo: shoulders; patrón: neck press |
| `Olympic_Squat` | Olympic Squat | quadriceps | patrón: squat |
| `One-Arm_Dumbbell_Row` | One-Arm Dumbbell Row | middle back | músculo: middle back; músculo: lats; músculo: shoulders; patrón: row |
| `One-Arm_Flat_Bench_Dumbbell_Flye` | One-Arm Flat Bench Dumbbell Flye | chest | músculo: chest; patrón: fly; patrón: flye |
| `One-Arm_High-Pulley_Cable_Side_Bends` | One-Arm High-Pulley Cable Side Bends | abdominals | patrón: high pulley |
| `One-Arm_Incline_Lateral_Raise` | One-Arm Incline Lateral Raise | shoulders | músculo: shoulders; patrón: raise |
| `One-Arm_Kettlebell_Clean` | One-Arm Kettlebell Clean | hamstrings | músculo: shoulders; músculo: traps; patrón: clean |
| `One-Arm_Kettlebell_Clean_and_Jerk` | One-Arm Kettlebell Clean and Jerk | shoulders | músculo: shoulders; patrón: jerk; patrón: clean |
| `One-Arm_Kettlebell_Floor_Press` | One-Arm Kettlebell Floor Press | chest | músculo: chest; patrón: floor press |
| `One-Arm_Kettlebell_Jerk` | One-Arm Kettlebell Jerk | shoulders | músculo: shoulders; patrón: jerk |
| `One-Arm_Kettlebell_Military_Press_To_The_Side` | One-Arm Kettlebell Military Press To The Side | shoulders | músculo: shoulders; patrón: military |
| `One-Arm_Kettlebell_Para_Press` | One-Arm Kettlebell Para Press | shoulders | músculo: shoulders |
| `One-Arm_Kettlebell_Push_Press` | One-Arm Kettlebell Push Press | shoulders | músculo: shoulders; patrón: push press |
| `One-Arm_Kettlebell_Row` | One-Arm Kettlebell Row | middle back | músculo: middle back; músculo: lats; patrón: row |
| `One-Arm_Kettlebell_Snatch` | One-Arm Kettlebell Snatch | shoulders | músculo: shoulders; músculo: traps; patrón: snatch |
| `One-Arm_Kettlebell_Split_Jerk` | One-Arm Kettlebell Split Jerk | shoulders | músculo: shoulders; patrón: jerk |
| `One-Arm_Kettlebell_Split_Snatch` | One-Arm Kettlebell Split Snatch | shoulders | músculo: shoulders; patrón: snatch |
| `One-Arm_Kettlebell_Swings` | One-Arm Kettlebell Swings | hamstrings | músculo: shoulders; patrón: swing |
| `One-Arm_Long_Bar_Row` | One-Arm Long Bar Row | middle back | músculo: middle back; músculo: lats; patrón: row |
| `One-Arm_Medicine_Ball_Slam` | One-Arm Medicine Ball Slam | abdominals | músculo: lats; músculo: shoulders; patrón: slam; patrón: medicine ball |
| `One-Arm_Open_Palm_Kettlebell_Clean` | One-Arm Open Palm Kettlebell Clean | hamstrings | músculo: shoulders; patrón: clean |
| `One-Arm_Overhead_Kettlebell_Squats` | One-Arm Overhead Kettlebell Squats | quadriceps | músculo: shoulders; patrón: overhead; patrón: squat |
| `One-Arm_Side_Deadlift` | One-Arm Side Deadlift | quadriceps | músculo: traps; patrón: deadlift |
| `One-Arm_Side_Laterals` | One-Arm Side Laterals | shoulders | músculo: shoulders |
| `One-Legged_Cable_Kickback` | One-Legged Cable Kickback | glutes | patrón: kickback |
| `One_Arm_Against_Wall` | One Arm Against Wall | lats | músculo: lats; patrón: against wall |
| `One_Arm_Chin-Up` | One Arm Chin-Up | middle back | músculo: middle back; músculo: lats; patrón: chin up; patrón: chinup |
| `One_Arm_Dumbbell_Bench_Press` | One Arm Dumbbell Bench Press | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `One_Arm_Floor_Press` | One Arm Floor Press | triceps | músculo: chest; músculo: shoulders; patrón: floor press |
| `One_Arm_Lat_Pulldown` | One Arm Lat Pulldown | lats | músculo: lats; músculo: middle back; patrón: pulldown |
| `One_Arm_Pronated_Dumbbell_Triceps_Extension` | One Arm Pronated Dumbbell Triceps Extension | triceps | patrón: triceps extension |
| `One_Arm_Supinated_Dumbbell_Triceps_Extension` | One Arm Supinated Dumbbell Triceps Extension | triceps | patrón: triceps extension |
| `One_Half_Locust` | One Half Locust | quadriceps | músculo: chest |
| `One_Handed_Hang` | One Handed Hang | lats | músculo: lats; patrón: hang |
| `One_Leg_Barbell_Squat` | One Leg Barbell Squat | quadriceps | patrón: squat |
| `Open_Palm_Kettlebell_Clean` | Open Palm Kettlebell Clean | hamstrings | músculo: shoulders; patrón: clean |
| `Otis-Up` | Otis-Up | abdominals | músculo: chest; músculo: shoulders |
| `Overhead_Cable_Curl` | Overhead Cable Curl | biceps | patrón: overhead |
| `Overhead_Lat` | Overhead Lat | lats | músculo: lats; patrón: overhead |
| `Overhead_Slam` | Overhead Slam | lats | músculo: lats; patrón: overhead; patrón: slam |
| `Overhead_Squat` | Overhead Squat | quadriceps | músculo: shoulders; patrón: overhead; patrón: squat |
| `Overhead_Stretch` | Overhead Stretch | abdominals | músculo: chest; músculo: lats; patrón: overhead |
| `Overhead_Triceps` | Overhead Triceps | triceps | músculo: lats; patrón: overhead |
| `Pallof_Press` | Pallof Press | abdominals | músculo: chest; músculo: shoulders |
| `Pallof_Press_With_Rotation` | Pallof Press With Rotation | abdominals | músculo: chest; músculo: shoulders; patrón: rotation |
| `Parallel_Bar_Dip` | Parallel Bar Dip | triceps | músculo: chest; músculo: shoulders; patrón: dip |
| `Pin_Presses` | Pin Presses | triceps | músculo: chest; músculo: lats; músculo: middle back; músculo: shoulders |
| `Plank` | Plank | abdominals | patrón: plank |
| `Plie_Dumbbell_Squat` | Plie Dumbbell Squat | quadriceps | patrón: squat |
| `Plyo_Kettlebell_Pushups` | Plyo Kettlebell Pushups | chest | músculo: chest; músculo: shoulders; patrón: yoke; patrón: push up; patrón: pushup |
| `Plyo_Push-up` | Plyo Push-up | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Power_Clean` | Power Clean | hamstrings | músculo: middle back; músculo: shoulders; músculo: traps; patrón: clean |
| `Power_Clean_from_Blocks` | Power Clean from Blocks | hamstrings | patrón: clean |
| `Power_Jerk` | Power Jerk | quadriceps | músculo: shoulders; patrón: jerk |
| `Power_Partials` | Power Partials | shoulders | músculo: shoulders; patrón: power partials |
| `Power_Snatch` | Power Snatch | hamstrings | músculo: shoulders; músculo: traps; patrón: snatch |
| `Power_Snatch_from_Blocks` | Power Snatch from Blocks | quadriceps | músculo: shoulders; músculo: traps; patrón: snatch |
| `Power_Stairs` | Power Stairs | hamstrings | músculo: shoulders; músculo: traps |
| `Press_Sit-Up` | Press Sit-Up | abdominals | músculo: chest; músculo: shoulders |
| `Prowler_Sprint` | Prowler Sprint | hamstrings | músculo: chest; músculo: shoulders; patrón: row |
| `Pullups` | Pullups | lats | músculo: lats; músculo: middle back; patrón: pull up; patrón: pullup |
| `Push-Up_Wide` | Push-Up Wide | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Push-Ups_-_Close_Triceps_Position` | Push-Ups - Close Triceps Position | triceps | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Push-Ups_With_Feet_Elevated` | Push-Ups With Feet Elevated | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Push-Ups_With_Feet_On_An_Exercise_Ball` | Push-Ups With Feet On An Exercise Ball | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Push_Press` | Push Press | shoulders | músculo: shoulders; patrón: push press |
| `Push_Press_-_Behind_the_Neck` | Push Press - Behind the Neck | shoulders | músculo: shoulders; patrón: push press; patrón: behind the neck |
| `Push_Up_to_Side_Plank` | Push Up to Side Plank | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup; patrón: plank |
| `Pushups` | Pushups | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Pushups_Close_and_Wide_Hand_Positions` | Pushups (Close and Wide Hand Positions) | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Pyramid` | Pyramid | lower back | músculo: shoulders |
| `Rack_Delivery` | Rack Delivery | shoulders | músculo: shoulders; músculo: traps; patrón: rack delivery |
| `Rack_Pull_with_Bands` | Rack Pull with Bands | lower back | músculo: traps; patrón: rack pull |
| `Rack_Pulls` | Rack Pulls | lower back | músculo: traps; patrón: rack pull |
| `Rear_Leg_Raises` | Rear Leg Raises | quadriceps | patrón: raise |
| `Return_Push_from_Stance` | Return Push from Stance | shoulders | músculo: shoulders; músculo: chest |
| `Reverse_Band_Bench_Press` | Reverse Band Bench Press | triceps | músculo: chest; músculo: lats; músculo: middle back; músculo: shoulders; patrón: bench press |
| `Reverse_Band_Box_Squat` | Reverse Band Box Squat | quadriceps | patrón: squat |
| `Reverse_Band_Deadlift` | Reverse Band Deadlift | lower back | patrón: deadlift |
| `Reverse_Band_Power_Squat` | Reverse Band Power Squat | quadriceps | patrón: squat |
| `Reverse_Band_Sumo_Deadlift` | Reverse Band Sumo Deadlift | hamstrings | músculo: traps; patrón: deadlift |
| `Reverse_Flyes` | Reverse Flyes | shoulders | músculo: shoulders; patrón: fly; patrón: flye |
| `Reverse_Flyes_With_External_Rotation` | Reverse Flyes With External Rotation | shoulders | músculo: shoulders; patrón: fly; patrón: flye; patrón: rotation |
| `Reverse_Grip_Bent-Over_Rows` | Reverse Grip Bent-Over Rows | middle back | músculo: middle back; músculo: lats; músculo: shoulders; patrón: row |
| `Reverse_Machine_Flyes` | Reverse Machine Flyes | shoulders | músculo: shoulders; patrón: fly; patrón: flye |
| `Reverse_Triceps_Bench_Press` | Reverse Triceps Bench Press | triceps | músculo: chest; músculo: shoulders; patrón: bench press |
| `Rhomboids-SMR` | Rhomboids-SMR | middle back | músculo: middle back; músculo: traps |
| `Rickshaw_Carry` | Rickshaw Carry | forearms | músculo: traps; patrón: rickshaw |
| `Rickshaw_Deadlift` | Rickshaw Deadlift | quadriceps | músculo: traps; patrón: deadlift; patrón: rickshaw |
| `Ring_Dips` | Ring Dips | triceps | músculo: chest; músculo: shoulders; patrón: dip |
| `Rocking_Standing_Calf_Raise` | Rocking Standing Calf Raise | calves | patrón: raise |
| `Rocky_Pull-Ups_Pulldowns` | Rocky Pull-Ups/Pulldowns | lats | músculo: lats; músculo: middle back; músculo: shoulders; patrón: pull up; patrón: pullup; patrón: pulldown |
| `Romanian_Deadlift` | Romanian Deadlift | hamstrings | patrón: deadlift |
| `Romanian_Deadlift_from_Deficit` | Romanian Deadlift from Deficit | hamstrings | músculo: traps; patrón: deadlift |
| `Rope_Climb` | Rope Climb | lats | músculo: lats; músculo: middle back; músculo: shoulders; patrón: rope |
| `Rope_Crunch` | Rope Crunch | abdominals | patrón: rope |
| `Rope_Jumping` | Rope Jumping | quadriceps | patrón: rope |
| `Rope_Straight-Arm_Pulldown` | Rope Straight-Arm Pulldown | lats | músculo: lats; patrón: pulldown; patrón: rope |
| `Round_The_World_Shoulder_Stretch` | Round The World Shoulder Stretch | shoulders | músculo: shoulders; músculo: chest |
| `Rowing_Stationary` | Rowing, Stationary | quadriceps | músculo: middle back; patrón: row |
| `Sandbag_Load` | Sandbag Load | quadriceps | músculo: middle back; músculo: shoulders; músculo: traps |
| `Scapular_Pull-Up` | Scapular Pull-Up | traps | músculo: traps; músculo: lats; músculo: middle back; patrón: pull up; patrón: pullup |
| `Seated_Barbell_Military_Press` | Seated Barbell Military Press | shoulders | músculo: shoulders; patrón: military |
| `Seated_Bent-Over_One-Arm_Dumbbell_Triceps_Extension` | Seated Bent-Over One-Arm Dumbbell Triceps Extension | triceps | patrón: triceps extension |
| `Seated_Bent-Over_Rear_Delt_Raise` | Seated Bent-Over Rear Delt Raise | shoulders | músculo: shoulders; patrón: raise |
| `Seated_Bent-Over_Two-Arm_Dumbbell_Triceps_Extension` | Seated Bent-Over Two-Arm Dumbbell Triceps Extension | triceps | patrón: triceps extension |
| `Seated_Biceps` | Seated Biceps | biceps | músculo: chest; músculo: shoulders |
| `Seated_Cable_Rows` | Seated Cable Rows | middle back | músculo: middle back; músculo: lats; músculo: shoulders; patrón: row |
| `Seated_Cable_Shoulder_Press` | Seated Cable Shoulder Press | shoulders | músculo: shoulders; patrón: shoulder press |
| `Seated_Calf_Raise` | Seated Calf Raise | calves | patrón: raise |
| `Seated_Dumbbell_Press` | Seated Dumbbell Press | shoulders | músculo: shoulders |
| `Seated_Front_Deltoid` | Seated Front Deltoid | shoulders | músculo: shoulders; músculo: chest |
| `Seated_Good_Mornings` | Seated Good Mornings | lower back | patrón: good morning |
| `Seated_One-arm_Cable_Pulley_Rows` | Seated One-arm Cable Pulley Rows | middle back | músculo: middle back; músculo: lats; músculo: traps; patrón: row |
| `Seated_Overhead_Stretch` | Seated Overhead Stretch | abdominals | patrón: overhead |
| `Seated_Side_Lateral_Raise` | Seated Side Lateral Raise | shoulders | músculo: shoulders; patrón: raise |
| `Seated_Triceps_Press` | Seated Triceps Press | triceps | patrón: triceps press |
| `See-Saw_Press_Alternating_Side_Press` | See-Saw Press (Alternating Side Press) | shoulders | músculo: shoulders |
| `Shotgun_Row` | Shotgun Row | lats | músculo: lats; músculo: middle back; patrón: row |
| `Shoulder_Circles` | Shoulder Circles | shoulders | músculo: shoulders; músculo: traps; patrón: circles |
| `Shoulder_Press_-_With_Bands` | Shoulder Press - With Bands | shoulders | músculo: shoulders; patrón: shoulder press |
| `Shoulder_Raise` | Shoulder Raise | shoulders | músculo: shoulders; músculo: lats; patrón: raise |
| `Shoulder_Stretch` | Shoulder Stretch | shoulders | músculo: shoulders |
| `Side-Lying_Floor_Stretch` | Side-Lying Floor Stretch | lats | músculo: lats |
| `Side_Bridge` | Side Bridge | abdominals | músculo: shoulders |
| `Side_Lateral_Raise` | Side Lateral Raise | shoulders | músculo: shoulders; patrón: raise |
| `Side_Laterals_to_Front_Raise` | Side Laterals to Front Raise | shoulders | músculo: shoulders; músculo: traps; patrón: raise |
| `Side_Leg_Raises` | Side Leg Raises | adductors | patrón: raise |
| `Side_To_Side_Chins` | Side To Side Chins | lats | músculo: lats; músculo: middle back; músculo: shoulders; patrón: chins |
| `Side_Wrist_Pull` | Side Wrist Pull | shoulders | músculo: shoulders; músculo: lats |
| `Single-Arm_Cable_Crossover` | Single-Arm Cable Crossover | chest | músculo: chest; patrón: crossover |
| `Single-Arm_Linear_Jammer` | Single-Arm Linear Jammer | shoulders | músculo: shoulders; músculo: chest; patrón: jammer |
| `Single-Arm_Push-Up` | Single-Arm Push-Up | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Single-Leg_High_Box_Squat` | Single-Leg High Box Squat | quadriceps | patrón: squat |
| `Single_Dumbbell_Raise` | Single Dumbbell Raise | shoulders | músculo: shoulders; músculo: traps; patrón: raise |
| `Sit_Squats` | Sit Squats | quadriceps | patrón: squat |
| `Sled_Drag_-_Harness` | Sled Drag - Harness | quadriceps | patrón: sled |
| `Sled_Overhead_Backward_Walk` | Sled Overhead Backward Walk | shoulders | músculo: shoulders; músculo: middle back; patrón: overhead; patrón: sled |
| `Sled_Overhead_Triceps_Extension` | Sled Overhead Triceps Extension | triceps | patrón: overhead; patrón: triceps extension; patrón: sled |
| `Sled_Push` | Sled Push | quadriceps | músculo: chest; patrón: sled |
| `Sled_Reverse_Flye` | Sled Reverse Flye | shoulders | músculo: shoulders; patrón: fly; patrón: flye; patrón: sled |
| `Sled_Row` | Sled Row | middle back | músculo: middle back; músculo: lats; patrón: row; patrón: sled |
| `Sledgehammer_Swings` | Sledgehammer Swings | abdominals | músculo: lats; músculo: middle back; músculo: shoulders; patrón: swing; patrón: sled |
| `Smith_Incline_Shoulder_Raise` | Smith Incline Shoulder Raise | shoulders | músculo: shoulders; músculo: chest; patrón: raise |
| `Smith_Machine_Behind_the_Back_Shrug` | Smith Machine Behind the Back Shrug | traps | músculo: traps; músculo: shoulders; patrón: behind the back |
| `Smith_Machine_Bench_Press` | Smith Machine Bench Press | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Smith_Machine_Bent_Over_Row` | Smith Machine Bent Over Row | middle back | músculo: middle back; músculo: lats; músculo: shoulders; patrón: row |
| `Smith_Machine_Calf_Raise` | Smith Machine Calf Raise | calves | patrón: raise |
| `Smith_Machine_Close-Grip_Bench_Press` | Smith Machine Close-Grip Bench Press | triceps | músculo: chest; músculo: shoulders; patrón: bench press |
| `Smith_Machine_Decline_Press` | Smith Machine Decline Press | chest | músculo: chest; músculo: shoulders |
| `Smith_Machine_Hang_Power_Clean` | Smith Machine Hang Power Clean | hamstrings | músculo: shoulders; músculo: traps; patrón: clean; patrón: hang |
| `Smith_Machine_Hip_Raise` | Smith Machine Hip Raise | abdominals | patrón: raise |
| `Smith_Machine_Incline_Bench_Press` | Smith Machine Incline Bench Press | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Smith_Machine_One-Arm_Upright_Row` | Smith Machine One-Arm Upright Row | shoulders | músculo: shoulders; músculo: traps; patrón: upright row; patrón: row |
| `Smith_Machine_Overhead_Shoulder_Press` | Smith Machine Overhead Shoulder Press | shoulders | músculo: shoulders; patrón: overhead; patrón: shoulder press |
| `Smith_Machine_Pistol_Squat` | Smith Machine Pistol Squat | quadriceps | patrón: squat |
| `Smith_Machine_Reverse_Calf_Raises` | Smith Machine Reverse Calf Raises | calves | patrón: raise |
| `Smith_Machine_Squat` | Smith Machine Squat | quadriceps | patrón: squat |
| `Smith_Machine_Stiff-Legged_Deadlift` | Smith Machine Stiff-Legged Deadlift | hamstrings | patrón: deadlift |
| `Smith_Machine_Upright_Row` | Smith Machine Upright Row | traps | músculo: traps; músculo: middle back; músculo: shoulders; patrón: upright row; patrón: row |
| `Smith_Single-Leg_Split_Squat` | Smith Single-Leg Split Squat | quadriceps | patrón: squat |
| `Snatch` | Snatch | quadriceps | músculo: shoulders; músculo: traps; patrón: snatch |
| `Snatch_Balance` | Snatch Balance | quadriceps | músculo: shoulders; patrón: snatch |
| `Snatch_Deadlift` | Snatch Deadlift | hamstrings | músculo: traps; patrón: snatch; patrón: deadlift |
| `Snatch_Pull` | Snatch Pull | hamstrings | músculo: traps; patrón: snatch |
| `Snatch_Shrug` | Snatch Shrug | traps | músculo: traps; músculo: shoulders; patrón: snatch |
| `Snatch_from_Blocks` | Snatch from Blocks | quadriceps | músculo: shoulders; músculo: traps; patrón: snatch |
| `Speed_Band_Overhead_Triceps` | Speed Band Overhead Triceps | triceps | patrón: overhead |
| `Speed_Box_Squat` | Speed Box Squat | quadriceps | patrón: squat |
| `Speed_Squats` | Speed Squats | quadriceps | patrón: squat |
| `Spell_Caster` | Spell Caster | abdominals | músculo: shoulders |
| `Spider_Crawl` | Spider Crawl | abdominals | músculo: chest; músculo: shoulders; patrón: crawl |
| `Spinal_Stretch` | Spinal Stretch | middle back | músculo: middle back; músculo: lats; músculo: traps |
| `Split_Clean` | Split Clean | quadriceps | músculo: shoulders; músculo: traps; patrón: clean |
| `Split_Jerk` | Split Jerk | quadriceps | músculo: shoulders; patrón: jerk |
| `Split_Snatch` | Split Snatch | hamstrings | músculo: shoulders; músculo: traps; patrón: snatch |
| `Split_Squat_with_Dumbbells` | Split Squat with Dumbbells | quadriceps | patrón: squat |
| `Split_Squats` | Split Squats | hamstrings | patrón: squat |
| `Squat_Jerk` | Squat Jerk | quadriceps | músculo: shoulders; patrón: jerk; patrón: squat |
| `Squat_with_Bands` | Squat with Bands | quadriceps | patrón: squat |
| `Squat_with_Chains` | Squat with Chains | quadriceps | patrón: squat |
| `Squat_with_Plate_Movers` | Squat with Plate Movers | quadriceps | patrón: squat |
| `Squats_-_With_Bands` | Squats - With Bands | quadriceps | patrón: squat |
| `Standing_Alternating_Dumbbell_Press` | Standing Alternating Dumbbell Press | shoulders | músculo: shoulders |
| `Standing_Barbell_Calf_Raise` | Standing Barbell Calf Raise | calves | patrón: raise |
| `Standing_Barbell_Press_Behind_Neck` | Standing Barbell Press Behind Neck | shoulders | músculo: shoulders; patrón: behind neck |
| `Standing_Bent-Over_One-Arm_Dumbbell_Triceps_Extension` | Standing Bent-Over One-Arm Dumbbell Triceps Extension | triceps | músculo: shoulders; patrón: triceps extension |
| `Standing_Bent-Over_Two-Arm_Dumbbell_Triceps_Extension` | Standing Bent-Over Two-Arm Dumbbell Triceps Extension | triceps | patrón: triceps extension |
| `Standing_Biceps_Stretch` | Standing Biceps Stretch | biceps | músculo: chest; músculo: shoulders; patrón: biceps stretch |
| `Standing_Bradford_Press` | Standing Bradford Press | shoulders | músculo: shoulders |
| `Standing_Cable_Chest_Press` | Standing Cable Chest Press | chest | músculo: chest; músculo: shoulders; patrón: chest press |
| `Standing_Cable_Lift` | Standing Cable Lift | abdominals | músculo: shoulders |
| `Standing_Cable_Wood_Chop` | Standing Cable Wood Chop | abdominals | músculo: shoulders |
| `Standing_Calf_Raises` | Standing Calf Raises | calves | patrón: raise |
| `Standing_Dumbbell_Calf_Raise` | Standing Dumbbell Calf Raise | calves | patrón: raise |
| `Standing_Dumbbell_Press` | Standing Dumbbell Press | shoulders | músculo: shoulders |
| `Standing_Dumbbell_Straight-Arm_Front_Delt_Raise_Above_Head` | Standing Dumbbell Straight-Arm Front Delt Raise Above Head | shoulders | músculo: shoulders; patrón: raise |
| `Standing_Dumbbell_Triceps_Extension` | Standing Dumbbell Triceps Extension | triceps | patrón: triceps extension |
| `Standing_Dumbbell_Upright_Row` | Standing Dumbbell Upright Row | traps | músculo: traps; músculo: shoulders; patrón: upright row; patrón: row |
| `Standing_Front_Barbell_Raise_Over_Head` | Standing Front Barbell Raise Over Head | shoulders | músculo: shoulders; patrón: overhead; patrón: raise |
| `Standing_Hip_Circles` | Standing Hip Circles | abductors | patrón: circles |
| `Standing_Low-Pulley_Deltoid_Raise` | Standing Low-Pulley Deltoid Raise | shoulders | músculo: shoulders; patrón: raise |
| `Standing_Low-Pulley_One-Arm_Triceps_Extension` | Standing Low-Pulley One-Arm Triceps Extension | triceps | músculo: chest; músculo: shoulders; patrón: triceps extension |
| `Standing_Military_Press` | Standing Military Press | shoulders | músculo: shoulders; patrón: military |
| `Standing_One-Arm_Dumbbell_Triceps_Extension` | Standing One-Arm Dumbbell Triceps Extension | triceps | músculo: chest; músculo: shoulders; patrón: triceps extension |
| `Standing_Overhead_Barbell_Triceps_Extension` | Standing Overhead Barbell Triceps Extension | triceps | músculo: shoulders; patrón: overhead; patrón: triceps extension |
| `Standing_Palm-In_One-Arm_Dumbbell_Press` | Standing Palm-In One-Arm Dumbbell Press | shoulders | músculo: shoulders |
| `Standing_Palms-In_Dumbbell_Press` | Standing Palms-In Dumbbell Press | shoulders | músculo: shoulders |
| `Standing_Palms-Up_Barbell_Behind_The_Back_Wrist_Curl` | Standing Palms-Up Barbell Behind The Back Wrist Curl | forearms | patrón: behind the back |
| `Standing_Rope_Crunch` | Standing Rope Crunch | abdominals | patrón: rope |
| `Standing_Towel_Triceps_Extension` | Standing Towel Triceps Extension | triceps | patrón: triceps extension |
| `Standing_Two-Arm_Overhead_Throw` | Standing Two-Arm Overhead Throw | shoulders | músculo: shoulders; músculo: chest; músculo: lats; patrón: overhead; patrón: row; patrón: throw |
| `Star_Jump` | Star Jump | quadriceps | músculo: shoulders |
| `Step-up_with_Knee_Raise` | Step-up with Knee Raise | glutes | patrón: raise |
| `Stiff-Legged_Barbell_Deadlift` | Stiff-Legged Barbell Deadlift | hamstrings | patrón: deadlift |
| `Stiff-Legged_Dumbbell_Deadlift` | Stiff-Legged Dumbbell Deadlift | hamstrings | patrón: deadlift |
| `Stiff_Leg_Barbell_Good_Morning` | Stiff Leg Barbell Good Morning | lower back | patrón: good morning |
| `Straight-Arm_Dumbbell_Pullover` | Straight-Arm Dumbbell Pullover | chest | músculo: chest; músculo: lats; músculo: shoulders; patrón: pullover |
| `Straight-Arm_Pulldown` | Straight-Arm Pulldown | lats | músculo: lats; patrón: pulldown |
| `Straight_Bar_Bench_Mid_Rows` | Straight Bar Bench Mid Rows | middle back | músculo: middle back; músculo: lats; patrón: row |
| `Straight_Raises_on_Incline_Bench` | Straight Raises on Incline Bench | shoulders | músculo: shoulders; músculo: traps; patrón: raise |
| `Stride_Jump_Crossover` | Stride Jump Crossover | quadriceps | patrón: crossover |
| `Sumo_Deadlift` | Sumo Deadlift | hamstrings | músculo: middle back; músculo: traps; patrón: deadlift |
| `Sumo_Deadlift_with_Bands` | Sumo Deadlift with Bands | hamstrings | músculo: middle back; músculo: traps; patrón: deadlift |
| `Sumo_Deadlift_with_Chains` | Sumo Deadlift with Chains | hamstrings | músculo: middle back; músculo: traps; patrón: deadlift |
| `Supine_Chest_Throw` | Supine Chest Throw | triceps | músculo: chest; músculo: shoulders; patrón: row; patrón: throw |
| `Supine_One-Arm_Overhead_Throw` | Supine One-Arm Overhead Throw | abdominals | músculo: chest; músculo: lats; músculo: shoulders; patrón: overhead; patrón: row; patrón: throw |
| `Supine_Two-Arm_Overhead_Throw` | Supine Two-Arm Overhead Throw | abdominals | músculo: chest; músculo: lats; músculo: shoulders; patrón: overhead; patrón: row; patrón: throw |
| `Suspended_Fallout` | Suspended Fallout | abdominals | músculo: chest; músculo: shoulders |
| `Suspended_Push-Up` | Suspended Push-Up | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Suspended_Row` | Suspended Row | middle back | músculo: middle back; músculo: lats; patrón: row |
| `Suspended_Split_Squat` | Suspended Split Squat | quadriceps | patrón: squat |
| `Svend_Press` | Svend Press | chest | músculo: chest; músculo: shoulders; patrón: svend |
| `T-Bar_Row_with_Handle` | T-Bar Row with Handle | middle back | músculo: middle back; músculo: lats; patrón: row |
| `Tate_Press` | Tate Press | triceps | músculo: chest; músculo: shoulders |
| `Tire_Flip` | Tire Flip | quadriceps | músculo: chest; músculo: shoulders; músculo: traps |
| `Torso_Rotation` | Torso Rotation | abdominals | patrón: rotation |
| `Trap_Bar_Deadlift` | Trap Bar Deadlift | quadriceps | patrón: deadlift |
| `Tricep_Dumbbell_Kickback` | Tricep Dumbbell Kickback | triceps | patrón: kickback |
| `Tricep_Side_Stretch` | Tricep Side Stretch | triceps | músculo: shoulders; patrón: tricep side stretch |
| `Triceps_Overhead_Extension_with_Rope` | Triceps Overhead Extension with Rope | triceps | patrón: overhead; patrón: rope |
| `Triceps_Pushdown_-_Rope_Attachment` | Triceps Pushdown - Rope Attachment | triceps | patrón: rope |
| `Triceps_Stretch` | Triceps Stretch | triceps | músculo: lats; patrón: triceps stretch |
| `Two-Arm_Kettlebell_Clean` | Two-Arm Kettlebell Clean | shoulders | músculo: shoulders; músculo: traps; patrón: clean |
| `Two-Arm_Kettlebell_Jerk` | Two-Arm Kettlebell Jerk | shoulders | músculo: shoulders; patrón: jerk |
| `Two-Arm_Kettlebell_Military_Press` | Two-Arm Kettlebell Military Press | shoulders | músculo: shoulders; patrón: military |
| `Two-Arm_Kettlebell_Row` | Two-Arm Kettlebell Row | middle back | músculo: middle back; músculo: lats; patrón: row |
| `Underhand_Cable_Pulldowns` | Underhand Cable Pulldowns | lats | músculo: lats; músculo: middle back; músculo: shoulders; patrón: pulldown |
| `Upper_Back-Leg_Grab` | Upper Back-Leg Grab | hamstrings | músculo: middle back |
| `Upper_Back_Stretch` | Upper Back Stretch | middle back | músculo: middle back |
| `Upright_Barbell_Row` | Upright Barbell Row | shoulders | músculo: shoulders; músculo: traps; patrón: row |
| `Upright_Cable_Row` | Upright Cable Row | traps | músculo: traps; músculo: shoulders; patrón: row |
| `Upright_Row_-_With_Bands` | Upright Row - With Bands | traps | músculo: traps; músculo: shoulders; patrón: upright row; patrón: row |
| `Upward_Stretch` | Upward Stretch | shoulders | músculo: shoulders; músculo: chest; músculo: lats |
| `V-Bar_Pulldown` | V-Bar Pulldown | lats | músculo: lats; músculo: middle back; músculo: shoulders; patrón: pulldown |
| `V-Bar_Pullup` | V-Bar Pullup | lats | músculo: lats; músculo: middle back; músculo: shoulders; patrón: pull up; patrón: pullup |
| `Vertical_Swing` | Vertical Swing | hamstrings | músculo: shoulders; patrón: swing |
| `Weighted_Ball_Hyperextension` | Weighted Ball Hyperextension | lower back | músculo: middle back |
| `Weighted_Bench_Dip` | Weighted Bench Dip | triceps | músculo: chest; músculo: shoulders; patrón: dip |
| `Weighted_Jump_Squat` | Weighted Jump Squat | quadriceps | patrón: squat |
| `Weighted_Pull_Ups` | Weighted Pull Ups | lats | músculo: lats; músculo: middle back; patrón: pull up; patrón: pullup |
| `Weighted_Sissy_Squat` | Weighted Sissy Squat | quadriceps | patrón: squat |
| `Weighted_Squat` | Weighted Squat | quadriceps | patrón: squat |
| `Wide-Grip_Barbell_Bench_Press` | Wide-Grip Barbell Bench Press | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Wide-Grip_Decline_Barbell_Bench_Press` | Wide-Grip Decline Barbell Bench Press | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Wide-Grip_Decline_Barbell_Pullover` | Wide-Grip Decline Barbell Pullover | chest | músculo: chest; músculo: shoulders; patrón: pullover |
| `Wide-Grip_Lat_Pulldown` | Wide-Grip Lat Pulldown | lats | músculo: lats; músculo: middle back; músculo: shoulders; patrón: pulldown |
| `Wide-Grip_Pulldown_Behind_The_Neck` | Wide-Grip Pulldown Behind The Neck | lats | músculo: lats; músculo: middle back; músculo: shoulders; patrón: behind the neck; patrón: pulldown |
| `Wide-Grip_Rear_Pull-Up` | Wide-Grip Rear Pull-Up | lats | músculo: lats; músculo: middle back; músculo: shoulders; patrón: pull up; patrón: pullup |
| `Wide_Stance_Barbell_Squat` | Wide Stance Barbell Squat | quadriceps | patrón: squat |
| `Wind_Sprints` | Wind Sprints | abdominals | patrón: wind sprint |
| `Windmills` | Windmills | abductors | patrón: windmill |
| `Wrist_Circles` | Wrist Circles | forearms | patrón: circles |
| `Wrist_Roller` | Wrist Roller | forearms | músculo: shoulders |
| `Wrist_Rotations_with_Straight_Bar` | Wrist Rotations with Straight Bar | forearms | patrón: rotation |
| `Yoke_Walk` | Yoke Walk | quadriceps | patrón: yoke |
| `Zercher_Squats` | Zercher Squats | quadriceps | patrón: squat |

## `hombro_izquierdo` (612 bloqueados)

- Músculos: chest, lats, middle back, shoulders, traps
- Patrones: `overhead`, `military`, `shoulder press`, `push press`, `arnold`, `upright row`, `behind the neck`, `behind neck`, `behind the head`, `behind the back`, `dip`, `handstand`, `snatch`, `jerk`, `clean`, `thruster`, `squat`, `good morning`, `barbell lunge`, `barbell walking lunge`, `barbell step`, `barbell side`, `deadlift`, `rack pull`, `farmer`, `rickshaw`, `yoke`, `pull up`, `pullup`, `chin up`, `chinup`, `chins`, `grip chin`, `gorilla chin`, `muscle up`, `pulldown`, `pullover`, `hang`, `row`, `raise`, `bench press`, `floor press`, `chest press`, `push up`, `pushup`, `body up`, `body tricep`, `triceps extension`, `tricep extension`, `triceps press`, `tricep press`, `skull`, `kickback`, `fly`, `flye`, `crossover`, `iron cross`, `crucifix`, `rotation`, `windmill`, `get up`, `getup`, `halo`, `throw`, `slam`, `swing`, `pike`, `plank`, `crawl`, `rope`, `log lift`, `atlas stone`, `renegade`, `london bridge`, `sled`, `jammer`, `landmine`, `incline dumbbell curl`, `incline hammer`, `incline inner`, `drag curl`, `high cable curl`, `high pulley`, `against wall`, `triceps stretch`, `tricep side stretch`, `biceps stretch`, `around the world`, `circles`, `chest push`, `chest pass`, `medicine ball`, `neck press`, `svend`, `power partials`, `rack delivery`, `inchworm`, `wind sprint`, `judo flip`, `chain handle`
- Ids extra: (ninguno)

| Id | Nombre | Músculo primario | Motivo |
|---|---|---|---|
| `Ab_Roller` | Ab Roller | abdominals | músculo: shoulders |
| `Advanced_Kettlebell_Windmill` | Advanced Kettlebell Windmill | abdominals | músculo: shoulders; patrón: windmill |
| `Alternate_Incline_Dumbbell_Curl` | Alternate Incline Dumbbell Curl | biceps | patrón: incline dumbbell curl |
| `Alternating_Cable_Shoulder_Press` | Alternating Cable Shoulder Press | shoulders | músculo: shoulders; patrón: shoulder press |
| `Alternating_Deltoid_Raise` | Alternating Deltoid Raise | shoulders | músculo: shoulders; patrón: raise |
| `Alternating_Floor_Press` | Alternating Floor Press | chest | músculo: chest; músculo: shoulders; patrón: floor press |
| `Alternating_Hang_Clean` | Alternating Hang Clean | hamstrings | músculo: traps; patrón: clean; patrón: hang |
| `Alternating_Kettlebell_Press` | Alternating Kettlebell Press | shoulders | músculo: shoulders |
| `Alternating_Kettlebell_Row` | Alternating Kettlebell Row | middle back | músculo: middle back; músculo: lats; patrón: row |
| `Alternating_Renegade_Row` | Alternating Renegade Row | middle back | músculo: middle back; músculo: chest; músculo: lats; patrón: row; patrón: renegade |
| `Ankle_Circles` | Ankle Circles | calves | patrón: circles |
| `Anti-Gravity_Press` | Anti-Gravity Press | shoulders | músculo: shoulders; músculo: middle back; músculo: traps |
| `Arm_Circles` | Arm Circles | shoulders | músculo: shoulders; músculo: traps; patrón: circles |
| `Arnold_Dumbbell_Press` | Arnold Dumbbell Press | shoulders | músculo: shoulders; patrón: arnold |
| `Around_The_Worlds` | Around The Worlds | chest | músculo: chest; músculo: shoulders; patrón: around the world |
| `Atlas_Stone_Trainer` | Atlas Stone Trainer | lower back | patrón: atlas stone |
| `Atlas_Stones` | Atlas Stones | lower back | músculo: middle back; músculo: traps; patrón: atlas stone |
| `Axle_Deadlift` | Axle Deadlift | lower back | músculo: middle back; músculo: traps; patrón: deadlift |
| `Back_Flyes_-_With_Bands` | Back Flyes - With Bands | shoulders | músculo: shoulders; músculo: middle back; patrón: fly; patrón: flye |
| `Backward_Medicine_Ball_Throw` | Backward Medicine Ball Throw | shoulders | músculo: shoulders; patrón: row; patrón: throw; patrón: medicine ball |
| `Band_Assisted_Pull-Up` | Band Assisted Pull-Up | lats | músculo: lats; músculo: middle back; patrón: pull up; patrón: pullup |
| `Band_Good_Morning` | Band Good Morning | hamstrings | patrón: good morning |
| `Band_Good_Morning_Pull_Through` | Band Good Morning (Pull Through) | hamstrings | patrón: good morning |
| `Band_Pull_Apart` | Band Pull Apart | shoulders | músculo: shoulders; músculo: middle back; músculo: traps |
| `Band_Skull_Crusher` | Band Skull Crusher | triceps | patrón: skull |
| `Barbell_Ab_Rollout` | Barbell Ab Rollout | abdominals | músculo: shoulders |
| `Barbell_Ab_Rollout_-_On_Knees` | Barbell Ab Rollout - On Knees | abdominals | músculo: shoulders |
| `Barbell_Bench_Press_-_Medium_Grip` | Barbell Bench Press - Medium Grip | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Barbell_Deadlift` | Barbell Deadlift | lower back | músculo: lats; músculo: middle back; músculo: traps; patrón: deadlift |
| `Barbell_Full_Squat` | Barbell Full Squat | quadriceps | patrón: squat |
| `Barbell_Guillotine_Bench_Press` | Barbell Guillotine Bench Press | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Barbell_Hack_Squat` | Barbell Hack Squat | quadriceps | patrón: squat |
| `Barbell_Incline_Bench_Press_-_Medium_Grip` | Barbell Incline Bench Press - Medium Grip | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Barbell_Incline_Shoulder_Raise` | Barbell Incline Shoulder Raise | shoulders | músculo: shoulders; músculo: chest; patrón: raise |
| `Barbell_Lunge` | Barbell Lunge | quadriceps | patrón: barbell lunge |
| `Barbell_Rear_Delt_Row` | Barbell Rear Delt Row | shoulders | músculo: shoulders; músculo: lats; músculo: middle back; patrón: row |
| `Barbell_Rollout_from_Bench` | Barbell Rollout from Bench | abdominals | músculo: lats; músculo: shoulders |
| `Barbell_Seated_Calf_Raise` | Barbell Seated Calf Raise | calves | patrón: raise |
| `Barbell_Shoulder_Press` | Barbell Shoulder Press | shoulders | músculo: shoulders; músculo: chest; patrón: shoulder press |
| `Barbell_Shrug` | Barbell Shrug | traps | músculo: traps |
| `Barbell_Shrug_Behind_The_Back` | Barbell Shrug Behind The Back | traps | músculo: traps; músculo: middle back; patrón: behind the back |
| `Barbell_Side_Bend` | Barbell Side Bend | abdominals | patrón: barbell side |
| `Barbell_Side_Split_Squat` | Barbell Side Split Squat | quadriceps | patrón: squat; patrón: barbell side |
| `Barbell_Squat` | Barbell Squat | quadriceps | patrón: squat |
| `Barbell_Squat_To_A_Bench` | Barbell Squat To A Bench | quadriceps | patrón: squat |
| `Barbell_Step_Ups` | Barbell Step Ups | quadriceps | patrón: barbell step |
| `Barbell_Walking_Lunge` | Barbell Walking Lunge | quadriceps | patrón: barbell walking lunge |
| `Battling_Ropes` | Battling Ropes | shoulders | músculo: shoulders; músculo: chest; patrón: rope |
| `Bear_Crawl_Sled_Drags` | Bear Crawl Sled Drags | quadriceps | patrón: crawl; patrón: sled |
| `Behind_Head_Chest_Stretch` | Behind Head Chest Stretch | chest | músculo: chest; músculo: shoulders |
| `Bench_Dips` | Bench Dips | triceps | músculo: chest; músculo: shoulders; patrón: dip |
| `Bench_Press_-_Powerlifting` | Bench Press - Powerlifting | triceps | músculo: chest; músculo: lats; músculo: shoulders; patrón: bench press |
| `Bench_Press_-_With_Bands` | Bench Press - With Bands | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Bench_Press_with_Chains` | Bench Press with Chains | triceps | músculo: chest; músculo: lats; músculo: shoulders; patrón: bench press |
| `Bent-Arm_Barbell_Pullover` | Bent-Arm Barbell Pullover | lats | músculo: lats; músculo: chest; músculo: shoulders; patrón: pullover |
| `Bent-Arm_Dumbbell_Pullover` | Bent-Arm Dumbbell Pullover | chest | músculo: chest; músculo: lats; músculo: shoulders; patrón: pullover |
| `Bent-Knee_Hip_Raise` | Bent-Knee Hip Raise | abdominals | patrón: raise |
| `Bent_Over_Barbell_Row` | Bent Over Barbell Row | middle back | músculo: middle back; músculo: lats; músculo: shoulders; patrón: row |
| `Bent_Over_Dumbbell_Rear_Delt_Raise_With_Head_On_Bench` | Bent Over Dumbbell Rear Delt Raise With Head On Bench | shoulders | músculo: shoulders; patrón: raise |
| `Bent_Over_Low-Pulley_Side_Lateral` | Bent Over Low-Pulley Side Lateral | shoulders | músculo: shoulders; músculo: middle back; músculo: traps |
| `Bent_Over_One-Arm_Long_Bar_Row` | Bent Over One-Arm Long Bar Row | middle back | músculo: middle back; músculo: lats; músculo: traps; patrón: row |
| `Bent_Over_Two-Arm_Long_Bar_Row` | Bent Over Two-Arm Long Bar Row | middle back | músculo: middle back; músculo: lats; patrón: row |
| `Bent_Over_Two-Dumbbell_Row` | Bent Over Two-Dumbbell Row | middle back | músculo: middle back; músculo: lats; músculo: shoulders; patrón: row |
| `Bent_Over_Two-Dumbbell_Row_With_Palms_In` | Bent Over Two-Dumbbell Row With Palms In | middle back | músculo: middle back; músculo: lats; patrón: row |
| `Bent_Press` | Bent Press | abdominals | músculo: shoulders |
| `Board_Press` | Board Press | triceps | músculo: chest; músculo: lats; músculo: shoulders |
| `Body-Up` | Body-Up | triceps | patrón: body up |
| `Body_Tricep_Press` | Body Tricep Press | triceps | patrón: body tricep; patrón: tricep press |
| `Bodyweight_Flyes` | Bodyweight Flyes | chest | músculo: chest; músculo: shoulders; patrón: fly; patrón: flye |
| `Bodyweight_Mid_Row` | Bodyweight Mid Row | middle back | músculo: middle back; músculo: lats; patrón: row |
| `Bodyweight_Squat` | Bodyweight Squat | quadriceps | patrón: squat |
| `Bottoms-Up_Clean_From_The_Hang_Position` | Bottoms-Up Clean From The Hang Position | forearms | músculo: shoulders; patrón: clean; patrón: hang |
| `Box_Squat` | Box Squat | quadriceps | patrón: squat |
| `Box_Squat_with_Bands` | Box Squat with Bands | quadriceps | patrón: squat |
| `Box_Squat_with_Chains` | Box Squat with Chains | quadriceps | patrón: squat |
| `Bradford_Rocky_Presses` | Bradford/Rocky Presses | shoulders | músculo: shoulders |
| `Butterfly` | Butterfly | chest | músculo: chest; patrón: fly |
| `Cable_Chest_Press` | Cable Chest Press | chest | músculo: chest; músculo: shoulders; patrón: chest press |
| `Cable_Crossover` | Cable Crossover | chest | músculo: chest; músculo: shoulders; patrón: crossover |
| `Cable_Deadlifts` | Cable Deadlifts | quadriceps | patrón: deadlift |
| `Cable_Hammer_Curls_-_Rope_Attachment` | Cable Hammer Curls - Rope Attachment | biceps | patrón: rope |
| `Cable_Incline_Pushdown` | Cable Incline Pushdown | lats | músculo: lats |
| `Cable_Incline_Triceps_Extension` | Cable Incline Triceps Extension | triceps | patrón: triceps extension |
| `Cable_Internal_Rotation` | Cable Internal Rotation | shoulders | músculo: shoulders; patrón: rotation |
| `Cable_Iron_Cross` | Cable Iron Cross | chest | músculo: chest; patrón: iron cross |
| `Cable_Judo_Flip` | Cable Judo Flip | abdominals | patrón: judo flip |
| `Cable_Lying_Triceps_Extension` | Cable Lying Triceps Extension | triceps | patrón: triceps extension |
| `Cable_One_Arm_Tricep_Extension` | Cable One Arm Tricep Extension | triceps | patrón: tricep extension |
| `Cable_Rear_Delt_Fly` | Cable Rear Delt Fly | shoulders | músculo: shoulders; patrón: fly |
| `Cable_Rope_Overhead_Triceps_Extension` | Cable Rope Overhead Triceps Extension | triceps | patrón: overhead; patrón: triceps extension; patrón: rope |
| `Cable_Rope_Rear-Delt_Rows` | Cable Rope Rear-Delt Rows | shoulders | músculo: shoulders; músculo: middle back; patrón: row; patrón: rope |
| `Cable_Seated_Lateral_Raise` | Cable Seated Lateral Raise | shoulders | músculo: shoulders; músculo: middle back; músculo: traps; patrón: raise |
| `Cable_Shoulder_Press` | Cable Shoulder Press | shoulders | músculo: shoulders; patrón: shoulder press |
| `Cable_Shrugs` | Cable Shrugs | traps | músculo: traps |
| `Calf-Machine_Shoulder_Shrug` | Calf-Machine Shoulder Shrug | traps | músculo: traps |
| `Calf_Raise_On_A_Dumbbell` | Calf Raise On A Dumbbell | calves | patrón: raise |
| `Calf_Raises_-_With_Bands` | Calf Raises - With Bands | calves | patrón: raise |
| `Calf_Stretch_Elbows_Against_Wall` | Calf Stretch Elbows Against Wall | calves | patrón: against wall |
| `Calf_Stretch_Hands_Against_Wall` | Calf Stretch Hands Against Wall | calves | patrón: against wall |
| `Car_Deadlift` | Car Deadlift | quadriceps | músculo: traps; patrón: deadlift |
| `Car_Drivers` | Car Drivers | shoulders | músculo: shoulders |
| `Cat_Stretch` | Cat Stretch | lower back | músculo: middle back; músculo: traps |
| `Catch_and_Overhead_Throw` | Catch and Overhead Throw | lats | músculo: lats; músculo: chest; músculo: shoulders; patrón: overhead; patrón: row; patrón: throw |
| `Chain_Handle_Extension` | Chain Handle Extension | triceps | patrón: chain handle |
| `Chain_Press` | Chain Press | chest | músculo: chest; músculo: shoulders |
| `Chair_Lower_Back_Stretch` | Chair Lower Back Stretch | lats | músculo: lats |
| `Chair_Squat` | Chair Squat | quadriceps | patrón: squat |
| `Chair_Upper_Body_Stretch` | Chair Upper Body Stretch | shoulders | músculo: shoulders; músculo: chest |
| `Chest_And_Front_Of_Shoulder_Stretch` | Chest And Front Of Shoulder Stretch | chest | músculo: chest; músculo: shoulders |
| `Chest_Push_from_3_point_stance` | Chest Push from 3 point stance | chest | músculo: chest; músculo: shoulders; patrón: chest push |
| `Chest_Push_multiple_response` | Chest Push (multiple response) | chest | músculo: chest; músculo: shoulders; patrón: chest push |
| `Chest_Push_single_response` | Chest Push (single response) | chest | músculo: chest; músculo: shoulders; patrón: chest push |
| `Chest_Push_with_Run_Release` | Chest Push with Run Release | chest | músculo: chest; músculo: shoulders; patrón: chest push |
| `Chest_Stretch_on_Stability_Ball` | Chest Stretch on Stability Ball | chest | músculo: chest |
| `Childs_Pose` | Child's Pose | lower back | músculo: middle back |
| `Chin-Up` | Chin-Up | lats | músculo: lats; músculo: middle back; patrón: chin up; patrón: chinup |
| `Chin_To_Chest_Stretch` | Chin To Chest Stretch | neck | músculo: traps |
| `Circus_Bell` | Circus Bell | shoulders | músculo: shoulders; músculo: traps |
| `Clean` | Clean | hamstrings | músculo: shoulders; músculo: traps; patrón: clean |
| `Clean_Deadlift` | Clean Deadlift | hamstrings | músculo: middle back; músculo: traps; patrón: clean; patrón: deadlift |
| `Clean_Pull` | Clean Pull | quadriceps | músculo: traps; patrón: clean |
| `Clean_Shrug` | Clean Shrug | traps | músculo: traps; músculo: shoulders; patrón: clean |
| `Clean_and_Jerk` | Clean and Jerk | shoulders | músculo: shoulders; músculo: traps; patrón: jerk; patrón: clean |
| `Clean_and_Press` | Clean and Press | shoulders | músculo: shoulders; músculo: middle back; músculo: traps; patrón: clean |
| `Clean_from_Blocks` | Clean from Blocks | quadriceps | músculo: shoulders; músculo: traps; patrón: clean |
| `Clock_Push-Up` | Clock Push-Up | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Close-Grip_Barbell_Bench_Press` | Close-Grip Barbell Bench Press | triceps | músculo: chest; músculo: shoulders; patrón: bench press |
| `Close-Grip_Dumbbell_Press` | Close-Grip Dumbbell Press | triceps | músculo: chest; músculo: shoulders |
| `Close-Grip_EZ-Bar_Press` | Close-Grip EZ-Bar Press | triceps | músculo: chest; músculo: shoulders |
| `Close-Grip_Front_Lat_Pulldown` | Close-Grip Front Lat Pulldown | lats | músculo: lats; músculo: middle back; músculo: shoulders; patrón: pulldown |
| `Close-Grip_Push-Up_off_of_a_Dumbbell` | Close-Grip Push-Up off of a Dumbbell | triceps | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Conans_Wheel` | Conan's Wheel | quadriceps | músculo: shoulders; músculo: traps |
| `Cross_Over_-_With_Bands` | Cross Over - With Bands | chest | músculo: chest; músculo: shoulders; patrón: crossover |
| `Crossover_Reverse_Lunge` | Crossover Reverse Lunge | lower back | patrón: crossover |
| `Crucifix` | Crucifix | shoulders | músculo: shoulders; patrón: crucifix |
| `Crunch_-_Hands_Overhead` | Crunch - Hands Overhead | abdominals | patrón: overhead |
| `Cuban_Press` | Cuban Press | shoulders | músculo: shoulders; músculo: traps |
| `Deadlift_with_Bands` | Deadlift with Bands | lower back | músculo: middle back; músculo: traps; patrón: deadlift |
| `Deadlift_with_Chains` | Deadlift with Chains | lower back | músculo: middle back; músculo: traps; patrón: deadlift |
| `Decline_Barbell_Bench_Press` | Decline Barbell Bench Press | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Decline_Close-Grip_Bench_To_Skull_Crusher` | Decline Close-Grip Bench To Skull Crusher | triceps | músculo: chest; músculo: shoulders; patrón: skull |
| `Decline_Dumbbell_Bench_Press` | Decline Dumbbell Bench Press | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Decline_Dumbbell_Flyes` | Decline Dumbbell Flyes | chest | músculo: chest; patrón: fly; patrón: flye |
| `Decline_Dumbbell_Triceps_Extension` | Decline Dumbbell Triceps Extension | triceps | patrón: triceps extension |
| `Decline_EZ_Bar_Triceps_Extension` | Decline EZ Bar Triceps Extension | triceps | patrón: triceps extension |
| `Decline_Push-Up` | Decline Push-Up | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Decline_Smith_Press` | Decline Smith Press | chest | músculo: chest; músculo: shoulders |
| `Deficit_Deadlift` | Deficit Deadlift | lower back | músculo: middle back; músculo: traps; patrón: deadlift |
| `Dip_Machine` | Dip Machine | triceps | músculo: chest; músculo: shoulders; patrón: dip |
| `Dips_-_Chest_Version` | Dips - Chest Version | chest | músculo: chest; músculo: shoulders; patrón: dip |
| `Dips_-_Triceps_Version` | Dips - Triceps Version | triceps | músculo: chest; músculo: shoulders; patrón: dip |
| `Donkey_Calf_Raises` | Donkey Calf Raises | calves | patrón: raise |
| `Double_Kettlebell_Alternating_Hang_Clean` | Double Kettlebell Alternating Hang Clean | hamstrings | músculo: traps; patrón: clean; patrón: hang |
| `Double_Kettlebell_Jerk` | Double Kettlebell Jerk | shoulders | músculo: shoulders; patrón: jerk |
| `Double_Kettlebell_Push_Press` | Double Kettlebell Push Press | shoulders | músculo: shoulders; patrón: push press |
| `Double_Kettlebell_Snatch` | Double Kettlebell Snatch | shoulders | músculo: shoulders; patrón: snatch |
| `Double_Kettlebell_Windmill` | Double Kettlebell Windmill | abdominals | músculo: shoulders; patrón: windmill |
| `Drag_Curl` | Drag Curl | biceps | patrón: drag curl |
| `Drop_Push` | Drop Push | chest | músculo: chest; músculo: shoulders |
| `Dumbbell_Bench_Press` | Dumbbell Bench Press | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Dumbbell_Bench_Press_with_Neutral_Grip` | Dumbbell Bench Press with Neutral Grip | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Dumbbell_Clean` | Dumbbell Clean | hamstrings | músculo: shoulders; músculo: traps; patrón: clean |
| `Dumbbell_Floor_Press` | Dumbbell Floor Press | triceps | músculo: chest; músculo: shoulders; patrón: floor press |
| `Dumbbell_Flyes` | Dumbbell Flyes | chest | músculo: chest; patrón: fly; patrón: flye |
| `Dumbbell_Incline_Row` | Dumbbell Incline Row | middle back | músculo: middle back; músculo: lats; músculo: shoulders; patrón: row |
| `Dumbbell_Incline_Shoulder_Raise` | Dumbbell Incline Shoulder Raise | shoulders | músculo: shoulders; patrón: raise |
| `Dumbbell_Lying_One-Arm_Rear_Lateral_Raise` | Dumbbell Lying One-Arm Rear Lateral Raise | shoulders | músculo: shoulders; músculo: middle back; patrón: raise |
| `Dumbbell_Lying_Rear_Lateral_Raise` | Dumbbell Lying Rear Lateral Raise | shoulders | músculo: shoulders; patrón: raise |
| `Dumbbell_One-Arm_Shoulder_Press` | Dumbbell One-Arm Shoulder Press | shoulders | músculo: shoulders; patrón: shoulder press |
| `Dumbbell_One-Arm_Triceps_Extension` | Dumbbell One-Arm Triceps Extension | triceps | patrón: triceps extension |
| `Dumbbell_One-Arm_Upright_Row` | Dumbbell One-Arm Upright Row | shoulders | músculo: shoulders; músculo: traps; patrón: upright row; patrón: row |
| `Dumbbell_Raise` | Dumbbell Raise | shoulders | músculo: shoulders; patrón: raise |
| `Dumbbell_Scaption` | Dumbbell Scaption | shoulders | músculo: shoulders; músculo: traps |
| `Dumbbell_Seated_One-Leg_Calf_Raise` | Dumbbell Seated One-Leg Calf Raise | calves | patrón: raise |
| `Dumbbell_Shoulder_Press` | Dumbbell Shoulder Press | shoulders | músculo: shoulders; patrón: shoulder press |
| `Dumbbell_Shrug` | Dumbbell Shrug | traps | músculo: traps |
| `Dumbbell_Squat` | Dumbbell Squat | quadriceps | patrón: squat |
| `Dumbbell_Squat_To_A_Bench` | Dumbbell Squat To A Bench | quadriceps | patrón: squat |
| `Dumbbell_Tricep_Extension_-Pronated_Grip` | Dumbbell Tricep Extension -Pronated Grip | triceps | patrón: tricep extension |
| `Dynamic_Back_Stretch` | Dynamic Back Stretch | lats | músculo: lats |
| `Dynamic_Chest_Stretch` | Dynamic Chest Stretch | chest | músculo: chest; músculo: middle back |
| `EZ-Bar_Skullcrusher` | EZ-Bar Skullcrusher | triceps | patrón: skull |
| `Elbow_Circles` | Elbow Circles | shoulders | músculo: shoulders; músculo: traps; patrón: circles |
| `Elbows_Back` | Elbows Back | chest | músculo: chest; músculo: shoulders |
| `Elevated_Cable_Rows` | Elevated Cable Rows | lats | músculo: lats; músculo: middle back; músculo: traps; patrón: row |
| `Extended_Range_One-Arm_Kettlebell_Floor_Press` | Extended Range One-Arm Kettlebell Floor Press | chest | músculo: chest; músculo: shoulders; patrón: floor press |
| `External_Rotation` | External Rotation | shoulders | músculo: shoulders; patrón: rotation |
| `External_Rotation_with_Band` | External Rotation with Band | shoulders | músculo: shoulders; patrón: rotation |
| `External_Rotation_with_Cable` | External Rotation with Cable | shoulders | músculo: shoulders; patrón: rotation |
| `Face_Pull` | Face Pull | shoulders | músculo: shoulders; músculo: middle back |
| `Farmers_Walk` | Farmer's Walk | forearms | músculo: traps; patrón: farmer |
| `Flat_Bench_Cable_Flyes` | Flat Bench Cable Flyes | chest | músculo: chest; patrón: fly; patrón: flye |
| `Flat_Bench_Lying_Leg_Raise` | Flat Bench Lying Leg Raise | abdominals | patrón: raise |
| `Flexor_Incline_Dumbbell_Curls` | Flexor Incline Dumbbell Curls | biceps | patrón: incline dumbbell curl |
| `Floor_Glute-Ham_Raise` | Floor Glute-Ham Raise | hamstrings | patrón: raise |
| `Floor_Press` | Floor Press | triceps | músculo: chest; músculo: shoulders; patrón: floor press |
| `Floor_Press_with_Chains` | Floor Press with Chains | triceps | músculo: chest; músculo: shoulders; patrón: floor press |
| `Forward_Drag_with_Press` | Forward Drag with Press | chest | músculo: chest; músculo: shoulders |
| `Frankenstein_Squat` | Frankenstein Squat | quadriceps | patrón: squat |
| `Freehand_Jump_Squat` | Freehand Jump Squat | quadriceps | patrón: squat |
| `Front_Barbell_Squat` | Front Barbell Squat | quadriceps | patrón: squat |
| `Front_Barbell_Squat_To_A_Bench` | Front Barbell Squat To A Bench | quadriceps | patrón: squat |
| `Front_Cable_Raise` | Front Cable Raise | shoulders | músculo: shoulders; patrón: raise |
| `Front_Dumbbell_Raise` | Front Dumbbell Raise | shoulders | músculo: shoulders; patrón: raise |
| `Front_Incline_Dumbbell_Raise` | Front Incline Dumbbell Raise | shoulders | músculo: shoulders; patrón: raise |
| `Front_Leg_Raises` | Front Leg Raises | hamstrings | patrón: raise |
| `Front_Plate_Raise` | Front Plate Raise | shoulders | músculo: shoulders; patrón: raise |
| `Front_Raise_And_Pullover` | Front Raise And Pullover | chest | músculo: chest; músculo: lats; músculo: shoulders; patrón: pullover; patrón: raise |
| `Front_Squat_Clean_Grip` | Front Squat (Clean Grip) | quadriceps | patrón: clean; patrón: squat |
| `Front_Squats_With_Two_Kettlebells` | Front Squats With Two Kettlebells | quadriceps | patrón: squat |
| `Front_Two-Dumbbell_Raise` | Front Two-Dumbbell Raise | shoulders | músculo: shoulders; patrón: raise |
| `Full_Range-Of-Motion_Lat_Pulldown` | Full Range-Of-Motion Lat Pulldown | lats | músculo: lats; músculo: middle back; músculo: shoulders; patrón: pulldown |
| `Gironda_Sternum_Chins` | Gironda Sternum Chins | lats | músculo: lats; músculo: middle back; patrón: chins |
| `Glute_Ham_Raise` | Glute Ham Raise | hamstrings | patrón: raise |
| `Glute_Kickback` | Glute Kickback | glutes | patrón: kickback |
| `Goblet_Squat` | Goblet Squat | quadriceps | músculo: shoulders; patrón: squat |
| `Good_Morning` | Good Morning | hamstrings | patrón: good morning |
| `Good_Morning_off_Pins` | Good Morning off Pins | hamstrings | patrón: good morning |
| `Gorilla_Chin_Crunch` | Gorilla Chin/Crunch | abdominals | músculo: lats; patrón: gorilla chin |
| `Hack_Squat` | Hack Squat | quadriceps | patrón: squat |
| `Hammer_Grip_Incline_DB_Bench_Press` | Hammer Grip Incline DB Bench Press | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Handstand_Push-Ups` | Handstand Push-Ups | shoulders | músculo: shoulders; patrón: handstand; patrón: push up; patrón: pushup |
| `Hang_Clean` | Hang Clean | quadriceps | músculo: shoulders; músculo: traps; patrón: clean; patrón: hang |
| `Hang_Clean_-_Below_the_Knees` | Hang Clean - Below the Knees | quadriceps | músculo: shoulders; músculo: traps; patrón: clean; patrón: hang |
| `Hang_Snatch` | Hang Snatch | hamstrings | músculo: shoulders; músculo: traps; patrón: snatch; patrón: hang |
| `Hang_Snatch_-_Below_Knees` | Hang Snatch - Below Knees | hamstrings | músculo: shoulders; músculo: traps; patrón: snatch; patrón: hang |
| `Hanging_Bar_Good_Morning` | Hanging Bar Good Morning | hamstrings | patrón: good morning; patrón: hang |
| `Hanging_Leg_Raise` | Hanging Leg Raise | abdominals | patrón: hang; patrón: raise |
| `Hanging_Pike` | Hanging Pike | abdominals | patrón: hang; patrón: pike |
| `Heaving_Snatch_Balance` | Heaving Snatch Balance | quadriceps | músculo: shoulders; patrón: snatch |
| `Heavy_Bag_Thrust` | Heavy Bag Thrust | chest | músculo: chest; músculo: shoulders |
| `High_Cable_Curls` | High Cable Curls | biceps | patrón: high cable curl |
| `Hip_Circles_prone` | Hip Circles (prone) | abductors | patrón: circles |
| `Inchworm` | Inchworm | hamstrings | patrón: inchworm |
| `Incline_Barbell_Triceps_Extension` | Incline Barbell Triceps Extension | triceps | patrón: triceps extension |
| `Incline_Bench_Pull` | Incline Bench Pull | middle back | músculo: middle back; músculo: lats; músculo: shoulders |
| `Incline_Cable_Chest_Press` | Incline Cable Chest Press | chest | músculo: chest; músculo: shoulders; patrón: chest press |
| `Incline_Cable_Flye` | Incline Cable Flye | chest | músculo: chest; músculo: shoulders; patrón: fly; patrón: flye |
| `Incline_Dumbbell_Bench_With_Palms_Facing_In` | Incline Dumbbell Bench With Palms Facing In | chest | músculo: chest; músculo: shoulders |
| `Incline_Dumbbell_Curl` | Incline Dumbbell Curl | biceps | patrón: incline dumbbell curl |
| `Incline_Dumbbell_Flyes` | Incline Dumbbell Flyes | chest | músculo: chest; músculo: shoulders; patrón: fly; patrón: flye |
| `Incline_Dumbbell_Flyes_-_With_A_Twist` | Incline Dumbbell Flyes - With A Twist | chest | músculo: chest; músculo: shoulders; patrón: fly; patrón: flye |
| `Incline_Dumbbell_Press` | Incline Dumbbell Press | chest | músculo: chest; músculo: shoulders |
| `Incline_Hammer_Curls` | Incline Hammer Curls | biceps | patrón: incline hammer |
| `Incline_Inner_Biceps_Curl` | Incline Inner Biceps Curl | biceps | patrón: incline inner |
| `Incline_Push-Up` | Incline Push-Up | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Incline_Push-Up_Close-Grip` | Incline Push-Up Close-Grip | triceps | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Incline_Push-Up_Depth_Jump` | Incline Push-Up Depth Jump | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Incline_Push-Up_Medium` | Incline Push-Up Medium | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Incline_Push-Up_Reverse_Grip` | Incline Push-Up Reverse Grip | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Incline_Push-Up_Wide` | Incline Push-Up Wide | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Internal_Rotation_with_Band` | Internal Rotation with Band | shoulders | músculo: shoulders; patrón: rotation |
| `Inverted_Row` | Inverted Row | middle back | músculo: middle back; músculo: lats; patrón: row |
| `Inverted_Row_with_Straps` | Inverted Row with Straps | middle back | músculo: middle back; músculo: lats; patrón: row |
| `Iron_Cross` | Iron Cross | shoulders | músculo: shoulders; músculo: chest; músculo: traps; patrón: iron cross |
| `Iron_Crosses_stretch` | Iron Crosses (stretch) | quadriceps | patrón: iron cross |
| `Isometric_Chest_Squeezes` | Isometric Chest Squeezes | chest | músculo: chest; músculo: shoulders |
| `Isometric_Wipers` | Isometric Wipers | chest | músculo: chest; músculo: shoulders |
| `JM_Press` | JM Press | triceps | músculo: chest; músculo: shoulders |
| `Jefferson_Squats` | Jefferson Squats | quadriceps | músculo: traps; patrón: squat |
| `Jerk_Balance` | Jerk Balance | shoulders | músculo: shoulders; patrón: jerk |
| `Jerk_Dip_Squat` | Jerk Dip Squat | quadriceps | patrón: dip; patrón: jerk; patrón: squat |
| `Keg_Load` | Keg Load | lower back | músculo: middle back; músculo: shoulders; músculo: traps |
| `Kettlebell_Arnold_Press` | Kettlebell Arnold Press | shoulders | músculo: shoulders; patrón: arnold |
| `Kettlebell_Dead_Clean` | Kettlebell Dead Clean | hamstrings | músculo: traps; patrón: clean |
| `Kettlebell_Figure_8` | Kettlebell Figure 8 | abdominals | músculo: shoulders |
| `Kettlebell_Halo` | Kettlebell Halo | shoulders | músculo: shoulders; músculo: traps; músculo: middle back; patrón: halo |
| `Kettlebell_Halo_With_Overhead_Extension` | Kettlebell Halo with Overhead Extension | shoulders | músculo: shoulders; músculo: traps; músculo: middle back; patrón: overhead; patrón: halo |
| `Kettlebell_Hang_Clean` | Kettlebell Hang Clean | hamstrings | músculo: shoulders; músculo: traps; patrón: clean; patrón: hang |
| `Kettlebell_One-Legged_Deadlift` | Kettlebell One-Legged Deadlift | hamstrings | patrón: deadlift |
| `Kettlebell_Overhead_Triceps_Extension` | Kettlebell Overhead Triceps Extension | triceps | músculo: shoulders; patrón: overhead; patrón: triceps extension |
| `Kettlebell_Pass_Between_The_Legs` | Kettlebell Pass Between The Legs | abdominals | músculo: shoulders |
| `Kettlebell_Pirate_Ships` | Kettlebell Pirate Ships | shoulders | músculo: shoulders |
| `Kettlebell_Pistol_Squat` | Kettlebell Pistol Squat | quadriceps | músculo: shoulders; patrón: squat |
| `Kettlebell_Seated_Press` | Kettlebell Seated Press | shoulders | músculo: shoulders |
| `Kettlebell_Seesaw_Press` | Kettlebell Seesaw Press | shoulders | músculo: shoulders |
| `Kettlebell_Sumo_High_Pull` | Kettlebell Sumo High Pull | traps | músculo: traps; músculo: shoulders |
| `Kettlebell_Thruster` | Kettlebell Thruster | shoulders | músculo: shoulders; patrón: thruster |
| `Kettlebell_Turkish_Get-Up_Lunge_style` | Kettlebell Turkish Get-Up (Lunge style) | shoulders | músculo: shoulders; patrón: get up; patrón: getup |
| `Kettlebell_Turkish_Get-Up_Squat_style` | Kettlebell Turkish Get-Up (Squat style) | shoulders | músculo: shoulders; patrón: squat; patrón: get up; patrón: getup |
| `Kettlebell_Windmill` | Kettlebell Windmill | abdominals | músculo: shoulders; patrón: windmill |
| `Kipping_Muscle_Up` | Kipping Muscle Up | lats | músculo: lats; músculo: middle back; músculo: shoulders; músculo: traps; patrón: muscle up |
| `Knee_Circles` | Knee Circles | calves | patrón: circles |
| `Knee_Hip_Raise_On_Parallel_Bars` | Knee/Hip Raise On Parallel Bars | abdominals | patrón: raise |
| `Kneeling_Arm_Drill` | Kneeling Arm Drill | shoulders | músculo: shoulders |
| `Kneeling_Cable_Triceps_Extension` | Kneeling Cable Triceps Extension | triceps | patrón: triceps extension |
| `Kneeling_High_Pulley_Row` | Kneeling High Pulley Row | lats | músculo: lats; músculo: middle back; patrón: row; patrón: high pulley |
| `Kneeling_Jump_Squat` | Kneeling Jump Squat | glutes | patrón: squat |
| `Kneeling_Single-Arm_High_Pulley_Row` | Kneeling Single-Arm High Pulley Row | lats | músculo: lats; músculo: middle back; patrón: row; patrón: high pulley |
| `Kneeling_Squat` | Kneeling Squat | glutes | patrón: squat |
| `Landmine_180s` | Landmine 180's | abdominals | músculo: shoulders; patrón: landmine |
| `Landmine_Linear_Jammer` | Landmine Linear Jammer | shoulders | músculo: shoulders; músculo: chest; patrón: jammer; patrón: landmine |
| `Lateral_Raise_-_With_Bands` | Lateral Raise - With Bands | shoulders | músculo: shoulders; patrón: raise |
| `Latissimus_Dorsi-SMR` | Latissimus Dorsi-SMR | lats | músculo: lats |
| `Leg-Over_Floor_Press` | Leg-Over Floor Press | chest | músculo: chest; músculo: shoulders; patrón: floor press |
| `Leverage_Chest_Press` | Leverage Chest Press | chest | músculo: chest; músculo: shoulders; patrón: chest press |
| `Leverage_Deadlift` | Leverage Deadlift | quadriceps | patrón: deadlift |
| `Leverage_Decline_Chest_Press` | Leverage Decline Chest Press | chest | músculo: chest; músculo: shoulders; patrón: chest press |
| `Leverage_High_Row` | Leverage High Row | middle back | músculo: middle back; músculo: lats; patrón: row |
| `Leverage_Incline_Chest_Press` | Leverage Incline Chest Press | chest | músculo: chest; músculo: shoulders; patrón: chest press |
| `Leverage_Iso_Row` | Leverage Iso Row | lats | músculo: lats; músculo: middle back; patrón: row |
| `Leverage_Shoulder_Press` | Leverage Shoulder Press | shoulders | músculo: shoulders; patrón: shoulder press |
| `Leverage_Shrug` | Leverage Shrug | traps | músculo: traps |
| `Log_Lift` | Log Lift | shoulders | músculo: shoulders; músculo: chest; músculo: middle back; músculo: traps; patrón: log lift |
| `London_Bridges` | London Bridges | lats | músculo: lats; músculo: middle back; patrón: london bridge |
| `Low_Cable_Crossover` | Low Cable Crossover | chest | músculo: chest; músculo: shoulders; patrón: crossover |
| `Low_Cable_Triceps_Extension` | Low Cable Triceps Extension | triceps | patrón: triceps extension |
| `Low_Pulley_Row_To_Neck` | Low Pulley Row To Neck | shoulders | músculo: shoulders; músculo: middle back; músculo: traps; patrón: row |
| `Lying_Cambered_Barbell_Row` | Lying Cambered Barbell Row | middle back | músculo: middle back; músculo: lats; músculo: traps; patrón: row |
| `Lying_Close-Grip_Bar_Curl_On_High_Pulley` | Lying Close-Grip Bar Curl On High Pulley | biceps | patrón: high pulley |
| `Lying_Close-Grip_Barbell_Triceps_Extension_Behind_The_Head` | Lying Close-Grip Barbell Triceps Extension Behind The Head | triceps | patrón: behind the head; patrón: triceps extension |
| `Lying_Close-Grip_Barbell_Triceps_Press_To_Chin` | Lying Close-Grip Barbell Triceps Press To Chin | triceps | patrón: triceps press |
| `Lying_Crossover` | Lying Crossover | abductors | patrón: crossover |
| `Lying_Dumbbell_Tricep_Extension` | Lying Dumbbell Tricep Extension | triceps | músculo: chest; músculo: shoulders; patrón: tricep extension |
| `Lying_Machine_Squat` | Lying Machine Squat | quadriceps | patrón: squat |
| `Lying_One-Arm_Lateral_Raise` | Lying One-Arm Lateral Raise | shoulders | músculo: shoulders; patrón: raise |
| `Lying_Rear_Delt_Raise` | Lying Rear Delt Raise | shoulders | músculo: shoulders; patrón: raise |
| `Lying_T-Bar_Row` | Lying T-Bar Row | middle back | músculo: middle back; músculo: lats; patrón: row |
| `Lying_Triceps_Press` | Lying Triceps Press | triceps | patrón: triceps press |
| `Machine_Bench_Press` | Machine Bench Press | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Machine_Shoulder_Military_Press` | Machine Shoulder (Military) Press | shoulders | músculo: shoulders; patrón: military |
| `Machine_Triceps_Extension` | Machine Triceps Extension | triceps | patrón: triceps extension |
| `Medicine_Ball_Chest_Pass` | Medicine Ball Chest Pass | chest | músculo: chest; músculo: shoulders; patrón: chest pass; patrón: medicine ball |
| `Medicine_Ball_Full_Twist` | Medicine Ball Full Twist | abdominals | músculo: shoulders; patrón: medicine ball |
| `Medicine_Ball_Scoop_Throw` | Medicine Ball Scoop Throw | shoulders | músculo: shoulders; patrón: row; patrón: throw; patrón: medicine ball |
| `Middle_Back_Shrug` | Middle Back Shrug | middle back | músculo: middle back |
| `Middle_Back_Stretch` | Middle Back Stretch | middle back | músculo: middle back; músculo: lats |
| `Mixed_Grip_Chin` | Mixed Grip Chin | middle back | músculo: middle back; músculo: lats; patrón: grip chin |
| `Mountain_Climbers` | Mountain Climbers | quadriceps | músculo: chest; músculo: shoulders |
| `Muscle_Snatch` | Muscle Snatch | hamstrings | músculo: shoulders; patrón: snatch |
| `Muscle_Up` | Muscle Up | lats | músculo: lats; músculo: middle back; músculo: shoulders; músculo: traps; patrón: muscle up |
| `Narrow_Stance_Hack_Squats` | Narrow Stance Hack Squats | quadriceps | patrón: squat; patrón: row |
| `Narrow_Stance_Leg_Press` | Narrow Stance Leg Press | quadriceps | patrón: row |
| `Narrow_Stance_Squats` | Narrow Stance Squats | quadriceps | patrón: squat; patrón: row |
| `Natural_Glute_Ham_Raise` | Natural Glute Ham Raise | hamstrings | patrón: raise |
| `Neck_Press` | Neck Press | chest | músculo: chest; músculo: shoulders; patrón: neck press |
| `Olympic_Squat` | Olympic Squat | quadriceps | patrón: squat |
| `One-Arm_Dumbbell_Row` | One-Arm Dumbbell Row | middle back | músculo: middle back; músculo: lats; músculo: shoulders; patrón: row |
| `One-Arm_Flat_Bench_Dumbbell_Flye` | One-Arm Flat Bench Dumbbell Flye | chest | músculo: chest; patrón: fly; patrón: flye |
| `One-Arm_High-Pulley_Cable_Side_Bends` | One-Arm High-Pulley Cable Side Bends | abdominals | patrón: high pulley |
| `One-Arm_Incline_Lateral_Raise` | One-Arm Incline Lateral Raise | shoulders | músculo: shoulders; patrón: raise |
| `One-Arm_Kettlebell_Clean` | One-Arm Kettlebell Clean | hamstrings | músculo: shoulders; músculo: traps; patrón: clean |
| `One-Arm_Kettlebell_Clean_and_Jerk` | One-Arm Kettlebell Clean and Jerk | shoulders | músculo: shoulders; patrón: jerk; patrón: clean |
| `One-Arm_Kettlebell_Floor_Press` | One-Arm Kettlebell Floor Press | chest | músculo: chest; patrón: floor press |
| `One-Arm_Kettlebell_Jerk` | One-Arm Kettlebell Jerk | shoulders | músculo: shoulders; patrón: jerk |
| `One-Arm_Kettlebell_Military_Press_To_The_Side` | One-Arm Kettlebell Military Press To The Side | shoulders | músculo: shoulders; patrón: military |
| `One-Arm_Kettlebell_Para_Press` | One-Arm Kettlebell Para Press | shoulders | músculo: shoulders |
| `One-Arm_Kettlebell_Push_Press` | One-Arm Kettlebell Push Press | shoulders | músculo: shoulders; patrón: push press |
| `One-Arm_Kettlebell_Row` | One-Arm Kettlebell Row | middle back | músculo: middle back; músculo: lats; patrón: row |
| `One-Arm_Kettlebell_Snatch` | One-Arm Kettlebell Snatch | shoulders | músculo: shoulders; músculo: traps; patrón: snatch |
| `One-Arm_Kettlebell_Split_Jerk` | One-Arm Kettlebell Split Jerk | shoulders | músculo: shoulders; patrón: jerk |
| `One-Arm_Kettlebell_Split_Snatch` | One-Arm Kettlebell Split Snatch | shoulders | músculo: shoulders; patrón: snatch |
| `One-Arm_Kettlebell_Swings` | One-Arm Kettlebell Swings | hamstrings | músculo: shoulders; patrón: swing |
| `One-Arm_Long_Bar_Row` | One-Arm Long Bar Row | middle back | músculo: middle back; músculo: lats; patrón: row |
| `One-Arm_Medicine_Ball_Slam` | One-Arm Medicine Ball Slam | abdominals | músculo: lats; músculo: shoulders; patrón: slam; patrón: medicine ball |
| `One-Arm_Open_Palm_Kettlebell_Clean` | One-Arm Open Palm Kettlebell Clean | hamstrings | músculo: shoulders; patrón: clean |
| `One-Arm_Overhead_Kettlebell_Squats` | One-Arm Overhead Kettlebell Squats | quadriceps | músculo: shoulders; patrón: overhead; patrón: squat |
| `One-Arm_Side_Deadlift` | One-Arm Side Deadlift | quadriceps | músculo: traps; patrón: deadlift |
| `One-Arm_Side_Laterals` | One-Arm Side Laterals | shoulders | músculo: shoulders |
| `One-Legged_Cable_Kickback` | One-Legged Cable Kickback | glutes | patrón: kickback |
| `One_Arm_Against_Wall` | One Arm Against Wall | lats | músculo: lats; patrón: against wall |
| `One_Arm_Chin-Up` | One Arm Chin-Up | middle back | músculo: middle back; músculo: lats; patrón: chin up; patrón: chinup |
| `One_Arm_Dumbbell_Bench_Press` | One Arm Dumbbell Bench Press | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `One_Arm_Floor_Press` | One Arm Floor Press | triceps | músculo: chest; músculo: shoulders; patrón: floor press |
| `One_Arm_Lat_Pulldown` | One Arm Lat Pulldown | lats | músculo: lats; músculo: middle back; patrón: pulldown |
| `One_Arm_Pronated_Dumbbell_Triceps_Extension` | One Arm Pronated Dumbbell Triceps Extension | triceps | patrón: triceps extension |
| `One_Arm_Supinated_Dumbbell_Triceps_Extension` | One Arm Supinated Dumbbell Triceps Extension | triceps | patrón: triceps extension |
| `One_Half_Locust` | One Half Locust | quadriceps | músculo: chest |
| `One_Handed_Hang` | One Handed Hang | lats | músculo: lats; patrón: hang |
| `One_Leg_Barbell_Squat` | One Leg Barbell Squat | quadriceps | patrón: squat |
| `Open_Palm_Kettlebell_Clean` | Open Palm Kettlebell Clean | hamstrings | músculo: shoulders; patrón: clean |
| `Otis-Up` | Otis-Up | abdominals | músculo: chest; músculo: shoulders |
| `Overhead_Cable_Curl` | Overhead Cable Curl | biceps | patrón: overhead |
| `Overhead_Lat` | Overhead Lat | lats | músculo: lats; patrón: overhead |
| `Overhead_Slam` | Overhead Slam | lats | músculo: lats; patrón: overhead; patrón: slam |
| `Overhead_Squat` | Overhead Squat | quadriceps | músculo: shoulders; patrón: overhead; patrón: squat |
| `Overhead_Stretch` | Overhead Stretch | abdominals | músculo: chest; músculo: lats; patrón: overhead |
| `Overhead_Triceps` | Overhead Triceps | triceps | músculo: lats; patrón: overhead |
| `Pallof_Press` | Pallof Press | abdominals | músculo: chest; músculo: shoulders |
| `Pallof_Press_With_Rotation` | Pallof Press With Rotation | abdominals | músculo: chest; músculo: shoulders; patrón: rotation |
| `Parallel_Bar_Dip` | Parallel Bar Dip | triceps | músculo: chest; músculo: shoulders; patrón: dip |
| `Pin_Presses` | Pin Presses | triceps | músculo: chest; músculo: lats; músculo: middle back; músculo: shoulders |
| `Plank` | Plank | abdominals | patrón: plank |
| `Plie_Dumbbell_Squat` | Plie Dumbbell Squat | quadriceps | patrón: squat |
| `Plyo_Kettlebell_Pushups` | Plyo Kettlebell Pushups | chest | músculo: chest; músculo: shoulders; patrón: yoke; patrón: push up; patrón: pushup |
| `Plyo_Push-up` | Plyo Push-up | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Power_Clean` | Power Clean | hamstrings | músculo: middle back; músculo: shoulders; músculo: traps; patrón: clean |
| `Power_Clean_from_Blocks` | Power Clean from Blocks | hamstrings | patrón: clean |
| `Power_Jerk` | Power Jerk | quadriceps | músculo: shoulders; patrón: jerk |
| `Power_Partials` | Power Partials | shoulders | músculo: shoulders; patrón: power partials |
| `Power_Snatch` | Power Snatch | hamstrings | músculo: shoulders; músculo: traps; patrón: snatch |
| `Power_Snatch_from_Blocks` | Power Snatch from Blocks | quadriceps | músculo: shoulders; músculo: traps; patrón: snatch |
| `Power_Stairs` | Power Stairs | hamstrings | músculo: shoulders; músculo: traps |
| `Press_Sit-Up` | Press Sit-Up | abdominals | músculo: chest; músculo: shoulders |
| `Prowler_Sprint` | Prowler Sprint | hamstrings | músculo: chest; músculo: shoulders; patrón: row |
| `Pullups` | Pullups | lats | músculo: lats; músculo: middle back; patrón: pull up; patrón: pullup |
| `Push-Up_Wide` | Push-Up Wide | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Push-Ups_-_Close_Triceps_Position` | Push-Ups - Close Triceps Position | triceps | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Push-Ups_With_Feet_Elevated` | Push-Ups With Feet Elevated | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Push-Ups_With_Feet_On_An_Exercise_Ball` | Push-Ups With Feet On An Exercise Ball | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Push_Press` | Push Press | shoulders | músculo: shoulders; patrón: push press |
| `Push_Press_-_Behind_the_Neck` | Push Press - Behind the Neck | shoulders | músculo: shoulders; patrón: push press; patrón: behind the neck |
| `Push_Up_to_Side_Plank` | Push Up to Side Plank | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup; patrón: plank |
| `Pushups` | Pushups | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Pushups_Close_and_Wide_Hand_Positions` | Pushups (Close and Wide Hand Positions) | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Pyramid` | Pyramid | lower back | músculo: shoulders |
| `Rack_Delivery` | Rack Delivery | shoulders | músculo: shoulders; músculo: traps; patrón: rack delivery |
| `Rack_Pull_with_Bands` | Rack Pull with Bands | lower back | músculo: traps; patrón: rack pull |
| `Rack_Pulls` | Rack Pulls | lower back | músculo: traps; patrón: rack pull |
| `Rear_Leg_Raises` | Rear Leg Raises | quadriceps | patrón: raise |
| `Return_Push_from_Stance` | Return Push from Stance | shoulders | músculo: shoulders; músculo: chest |
| `Reverse_Band_Bench_Press` | Reverse Band Bench Press | triceps | músculo: chest; músculo: lats; músculo: middle back; músculo: shoulders; patrón: bench press |
| `Reverse_Band_Box_Squat` | Reverse Band Box Squat | quadriceps | patrón: squat |
| `Reverse_Band_Deadlift` | Reverse Band Deadlift | lower back | patrón: deadlift |
| `Reverse_Band_Power_Squat` | Reverse Band Power Squat | quadriceps | patrón: squat |
| `Reverse_Band_Sumo_Deadlift` | Reverse Band Sumo Deadlift | hamstrings | músculo: traps; patrón: deadlift |
| `Reverse_Flyes` | Reverse Flyes | shoulders | músculo: shoulders; patrón: fly; patrón: flye |
| `Reverse_Flyes_With_External_Rotation` | Reverse Flyes With External Rotation | shoulders | músculo: shoulders; patrón: fly; patrón: flye; patrón: rotation |
| `Reverse_Grip_Bent-Over_Rows` | Reverse Grip Bent-Over Rows | middle back | músculo: middle back; músculo: lats; músculo: shoulders; patrón: row |
| `Reverse_Machine_Flyes` | Reverse Machine Flyes | shoulders | músculo: shoulders; patrón: fly; patrón: flye |
| `Reverse_Triceps_Bench_Press` | Reverse Triceps Bench Press | triceps | músculo: chest; músculo: shoulders; patrón: bench press |
| `Rhomboids-SMR` | Rhomboids-SMR | middle back | músculo: middle back; músculo: traps |
| `Rickshaw_Carry` | Rickshaw Carry | forearms | músculo: traps; patrón: rickshaw |
| `Rickshaw_Deadlift` | Rickshaw Deadlift | quadriceps | músculo: traps; patrón: deadlift; patrón: rickshaw |
| `Ring_Dips` | Ring Dips | triceps | músculo: chest; músculo: shoulders; patrón: dip |
| `Rocking_Standing_Calf_Raise` | Rocking Standing Calf Raise | calves | patrón: raise |
| `Rocky_Pull-Ups_Pulldowns` | Rocky Pull-Ups/Pulldowns | lats | músculo: lats; músculo: middle back; músculo: shoulders; patrón: pull up; patrón: pullup; patrón: pulldown |
| `Romanian_Deadlift` | Romanian Deadlift | hamstrings | patrón: deadlift |
| `Romanian_Deadlift_from_Deficit` | Romanian Deadlift from Deficit | hamstrings | músculo: traps; patrón: deadlift |
| `Rope_Climb` | Rope Climb | lats | músculo: lats; músculo: middle back; músculo: shoulders; patrón: rope |
| `Rope_Crunch` | Rope Crunch | abdominals | patrón: rope |
| `Rope_Jumping` | Rope Jumping | quadriceps | patrón: rope |
| `Rope_Straight-Arm_Pulldown` | Rope Straight-Arm Pulldown | lats | músculo: lats; patrón: pulldown; patrón: rope |
| `Round_The_World_Shoulder_Stretch` | Round The World Shoulder Stretch | shoulders | músculo: shoulders; músculo: chest |
| `Rowing_Stationary` | Rowing, Stationary | quadriceps | músculo: middle back; patrón: row |
| `Sandbag_Load` | Sandbag Load | quadriceps | músculo: middle back; músculo: shoulders; músculo: traps |
| `Scapular_Pull-Up` | Scapular Pull-Up | traps | músculo: traps; músculo: lats; músculo: middle back; patrón: pull up; patrón: pullup |
| `Seated_Barbell_Military_Press` | Seated Barbell Military Press | shoulders | músculo: shoulders; patrón: military |
| `Seated_Bent-Over_One-Arm_Dumbbell_Triceps_Extension` | Seated Bent-Over One-Arm Dumbbell Triceps Extension | triceps | patrón: triceps extension |
| `Seated_Bent-Over_Rear_Delt_Raise` | Seated Bent-Over Rear Delt Raise | shoulders | músculo: shoulders; patrón: raise |
| `Seated_Bent-Over_Two-Arm_Dumbbell_Triceps_Extension` | Seated Bent-Over Two-Arm Dumbbell Triceps Extension | triceps | patrón: triceps extension |
| `Seated_Biceps` | Seated Biceps | biceps | músculo: chest; músculo: shoulders |
| `Seated_Cable_Rows` | Seated Cable Rows | middle back | músculo: middle back; músculo: lats; músculo: shoulders; patrón: row |
| `Seated_Cable_Shoulder_Press` | Seated Cable Shoulder Press | shoulders | músculo: shoulders; patrón: shoulder press |
| `Seated_Calf_Raise` | Seated Calf Raise | calves | patrón: raise |
| `Seated_Dumbbell_Press` | Seated Dumbbell Press | shoulders | músculo: shoulders |
| `Seated_Front_Deltoid` | Seated Front Deltoid | shoulders | músculo: shoulders; músculo: chest |
| `Seated_Good_Mornings` | Seated Good Mornings | lower back | patrón: good morning |
| `Seated_One-arm_Cable_Pulley_Rows` | Seated One-arm Cable Pulley Rows | middle back | músculo: middle back; músculo: lats; músculo: traps; patrón: row |
| `Seated_Overhead_Stretch` | Seated Overhead Stretch | abdominals | patrón: overhead |
| `Seated_Side_Lateral_Raise` | Seated Side Lateral Raise | shoulders | músculo: shoulders; patrón: raise |
| `Seated_Triceps_Press` | Seated Triceps Press | triceps | patrón: triceps press |
| `See-Saw_Press_Alternating_Side_Press` | See-Saw Press (Alternating Side Press) | shoulders | músculo: shoulders |
| `Shotgun_Row` | Shotgun Row | lats | músculo: lats; músculo: middle back; patrón: row |
| `Shoulder_Circles` | Shoulder Circles | shoulders | músculo: shoulders; músculo: traps; patrón: circles |
| `Shoulder_Press_-_With_Bands` | Shoulder Press - With Bands | shoulders | músculo: shoulders; patrón: shoulder press |
| `Shoulder_Raise` | Shoulder Raise | shoulders | músculo: shoulders; músculo: lats; patrón: raise |
| `Shoulder_Stretch` | Shoulder Stretch | shoulders | músculo: shoulders |
| `Side-Lying_Floor_Stretch` | Side-Lying Floor Stretch | lats | músculo: lats |
| `Side_Bridge` | Side Bridge | abdominals | músculo: shoulders |
| `Side_Lateral_Raise` | Side Lateral Raise | shoulders | músculo: shoulders; patrón: raise |
| `Side_Laterals_to_Front_Raise` | Side Laterals to Front Raise | shoulders | músculo: shoulders; músculo: traps; patrón: raise |
| `Side_Leg_Raises` | Side Leg Raises | adductors | patrón: raise |
| `Side_To_Side_Chins` | Side To Side Chins | lats | músculo: lats; músculo: middle back; músculo: shoulders; patrón: chins |
| `Side_Wrist_Pull` | Side Wrist Pull | shoulders | músculo: shoulders; músculo: lats |
| `Single-Arm_Cable_Crossover` | Single-Arm Cable Crossover | chest | músculo: chest; patrón: crossover |
| `Single-Arm_Linear_Jammer` | Single-Arm Linear Jammer | shoulders | músculo: shoulders; músculo: chest; patrón: jammer |
| `Single-Arm_Push-Up` | Single-Arm Push-Up | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Single-Leg_High_Box_Squat` | Single-Leg High Box Squat | quadriceps | patrón: squat |
| `Single_Dumbbell_Raise` | Single Dumbbell Raise | shoulders | músculo: shoulders; músculo: traps; patrón: raise |
| `Sit_Squats` | Sit Squats | quadriceps | patrón: squat |
| `Sled_Drag_-_Harness` | Sled Drag - Harness | quadriceps | patrón: sled |
| `Sled_Overhead_Backward_Walk` | Sled Overhead Backward Walk | shoulders | músculo: shoulders; músculo: middle back; patrón: overhead; patrón: sled |
| `Sled_Overhead_Triceps_Extension` | Sled Overhead Triceps Extension | triceps | patrón: overhead; patrón: triceps extension; patrón: sled |
| `Sled_Push` | Sled Push | quadriceps | músculo: chest; patrón: sled |
| `Sled_Reverse_Flye` | Sled Reverse Flye | shoulders | músculo: shoulders; patrón: fly; patrón: flye; patrón: sled |
| `Sled_Row` | Sled Row | middle back | músculo: middle back; músculo: lats; patrón: row; patrón: sled |
| `Sledgehammer_Swings` | Sledgehammer Swings | abdominals | músculo: lats; músculo: middle back; músculo: shoulders; patrón: swing; patrón: sled |
| `Smith_Incline_Shoulder_Raise` | Smith Incline Shoulder Raise | shoulders | músculo: shoulders; músculo: chest; patrón: raise |
| `Smith_Machine_Behind_the_Back_Shrug` | Smith Machine Behind the Back Shrug | traps | músculo: traps; músculo: shoulders; patrón: behind the back |
| `Smith_Machine_Bench_Press` | Smith Machine Bench Press | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Smith_Machine_Bent_Over_Row` | Smith Machine Bent Over Row | middle back | músculo: middle back; músculo: lats; músculo: shoulders; patrón: row |
| `Smith_Machine_Calf_Raise` | Smith Machine Calf Raise | calves | patrón: raise |
| `Smith_Machine_Close-Grip_Bench_Press` | Smith Machine Close-Grip Bench Press | triceps | músculo: chest; músculo: shoulders; patrón: bench press |
| `Smith_Machine_Decline_Press` | Smith Machine Decline Press | chest | músculo: chest; músculo: shoulders |
| `Smith_Machine_Hang_Power_Clean` | Smith Machine Hang Power Clean | hamstrings | músculo: shoulders; músculo: traps; patrón: clean; patrón: hang |
| `Smith_Machine_Hip_Raise` | Smith Machine Hip Raise | abdominals | patrón: raise |
| `Smith_Machine_Incline_Bench_Press` | Smith Machine Incline Bench Press | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Smith_Machine_One-Arm_Upright_Row` | Smith Machine One-Arm Upright Row | shoulders | músculo: shoulders; músculo: traps; patrón: upright row; patrón: row |
| `Smith_Machine_Overhead_Shoulder_Press` | Smith Machine Overhead Shoulder Press | shoulders | músculo: shoulders; patrón: overhead; patrón: shoulder press |
| `Smith_Machine_Pistol_Squat` | Smith Machine Pistol Squat | quadriceps | patrón: squat |
| `Smith_Machine_Reverse_Calf_Raises` | Smith Machine Reverse Calf Raises | calves | patrón: raise |
| `Smith_Machine_Squat` | Smith Machine Squat | quadriceps | patrón: squat |
| `Smith_Machine_Stiff-Legged_Deadlift` | Smith Machine Stiff-Legged Deadlift | hamstrings | patrón: deadlift |
| `Smith_Machine_Upright_Row` | Smith Machine Upright Row | traps | músculo: traps; músculo: middle back; músculo: shoulders; patrón: upright row; patrón: row |
| `Smith_Single-Leg_Split_Squat` | Smith Single-Leg Split Squat | quadriceps | patrón: squat |
| `Snatch` | Snatch | quadriceps | músculo: shoulders; músculo: traps; patrón: snatch |
| `Snatch_Balance` | Snatch Balance | quadriceps | músculo: shoulders; patrón: snatch |
| `Snatch_Deadlift` | Snatch Deadlift | hamstrings | músculo: traps; patrón: snatch; patrón: deadlift |
| `Snatch_Pull` | Snatch Pull | hamstrings | músculo: traps; patrón: snatch |
| `Snatch_Shrug` | Snatch Shrug | traps | músculo: traps; músculo: shoulders; patrón: snatch |
| `Snatch_from_Blocks` | Snatch from Blocks | quadriceps | músculo: shoulders; músculo: traps; patrón: snatch |
| `Speed_Band_Overhead_Triceps` | Speed Band Overhead Triceps | triceps | patrón: overhead |
| `Speed_Box_Squat` | Speed Box Squat | quadriceps | patrón: squat |
| `Speed_Squats` | Speed Squats | quadriceps | patrón: squat |
| `Spell_Caster` | Spell Caster | abdominals | músculo: shoulders |
| `Spider_Crawl` | Spider Crawl | abdominals | músculo: chest; músculo: shoulders; patrón: crawl |
| `Spinal_Stretch` | Spinal Stretch | middle back | músculo: middle back; músculo: lats; músculo: traps |
| `Split_Clean` | Split Clean | quadriceps | músculo: shoulders; músculo: traps; patrón: clean |
| `Split_Jerk` | Split Jerk | quadriceps | músculo: shoulders; patrón: jerk |
| `Split_Snatch` | Split Snatch | hamstrings | músculo: shoulders; músculo: traps; patrón: snatch |
| `Split_Squat_with_Dumbbells` | Split Squat with Dumbbells | quadriceps | patrón: squat |
| `Split_Squats` | Split Squats | hamstrings | patrón: squat |
| `Squat_Jerk` | Squat Jerk | quadriceps | músculo: shoulders; patrón: jerk; patrón: squat |
| `Squat_with_Bands` | Squat with Bands | quadriceps | patrón: squat |
| `Squat_with_Chains` | Squat with Chains | quadriceps | patrón: squat |
| `Squat_with_Plate_Movers` | Squat with Plate Movers | quadriceps | patrón: squat |
| `Squats_-_With_Bands` | Squats - With Bands | quadriceps | patrón: squat |
| `Standing_Alternating_Dumbbell_Press` | Standing Alternating Dumbbell Press | shoulders | músculo: shoulders |
| `Standing_Barbell_Calf_Raise` | Standing Barbell Calf Raise | calves | patrón: raise |
| `Standing_Barbell_Press_Behind_Neck` | Standing Barbell Press Behind Neck | shoulders | músculo: shoulders; patrón: behind neck |
| `Standing_Bent-Over_One-Arm_Dumbbell_Triceps_Extension` | Standing Bent-Over One-Arm Dumbbell Triceps Extension | triceps | músculo: shoulders; patrón: triceps extension |
| `Standing_Bent-Over_Two-Arm_Dumbbell_Triceps_Extension` | Standing Bent-Over Two-Arm Dumbbell Triceps Extension | triceps | patrón: triceps extension |
| `Standing_Biceps_Stretch` | Standing Biceps Stretch | biceps | músculo: chest; músculo: shoulders; patrón: biceps stretch |
| `Standing_Bradford_Press` | Standing Bradford Press | shoulders | músculo: shoulders |
| `Standing_Cable_Chest_Press` | Standing Cable Chest Press | chest | músculo: chest; músculo: shoulders; patrón: chest press |
| `Standing_Cable_Lift` | Standing Cable Lift | abdominals | músculo: shoulders |
| `Standing_Cable_Wood_Chop` | Standing Cable Wood Chop | abdominals | músculo: shoulders |
| `Standing_Calf_Raises` | Standing Calf Raises | calves | patrón: raise |
| `Standing_Dumbbell_Calf_Raise` | Standing Dumbbell Calf Raise | calves | patrón: raise |
| `Standing_Dumbbell_Press` | Standing Dumbbell Press | shoulders | músculo: shoulders |
| `Standing_Dumbbell_Straight-Arm_Front_Delt_Raise_Above_Head` | Standing Dumbbell Straight-Arm Front Delt Raise Above Head | shoulders | músculo: shoulders; patrón: raise |
| `Standing_Dumbbell_Triceps_Extension` | Standing Dumbbell Triceps Extension | triceps | patrón: triceps extension |
| `Standing_Dumbbell_Upright_Row` | Standing Dumbbell Upright Row | traps | músculo: traps; músculo: shoulders; patrón: upright row; patrón: row |
| `Standing_Front_Barbell_Raise_Over_Head` | Standing Front Barbell Raise Over Head | shoulders | músculo: shoulders; patrón: overhead; patrón: raise |
| `Standing_Hip_Circles` | Standing Hip Circles | abductors | patrón: circles |
| `Standing_Low-Pulley_Deltoid_Raise` | Standing Low-Pulley Deltoid Raise | shoulders | músculo: shoulders; patrón: raise |
| `Standing_Low-Pulley_One-Arm_Triceps_Extension` | Standing Low-Pulley One-Arm Triceps Extension | triceps | músculo: chest; músculo: shoulders; patrón: triceps extension |
| `Standing_Military_Press` | Standing Military Press | shoulders | músculo: shoulders; patrón: military |
| `Standing_One-Arm_Dumbbell_Triceps_Extension` | Standing One-Arm Dumbbell Triceps Extension | triceps | músculo: chest; músculo: shoulders; patrón: triceps extension |
| `Standing_Overhead_Barbell_Triceps_Extension` | Standing Overhead Barbell Triceps Extension | triceps | músculo: shoulders; patrón: overhead; patrón: triceps extension |
| `Standing_Palm-In_One-Arm_Dumbbell_Press` | Standing Palm-In One-Arm Dumbbell Press | shoulders | músculo: shoulders |
| `Standing_Palms-In_Dumbbell_Press` | Standing Palms-In Dumbbell Press | shoulders | músculo: shoulders |
| `Standing_Palms-Up_Barbell_Behind_The_Back_Wrist_Curl` | Standing Palms-Up Barbell Behind The Back Wrist Curl | forearms | patrón: behind the back |
| `Standing_Rope_Crunch` | Standing Rope Crunch | abdominals | patrón: rope |
| `Standing_Towel_Triceps_Extension` | Standing Towel Triceps Extension | triceps | patrón: triceps extension |
| `Standing_Two-Arm_Overhead_Throw` | Standing Two-Arm Overhead Throw | shoulders | músculo: shoulders; músculo: chest; músculo: lats; patrón: overhead; patrón: row; patrón: throw |
| `Star_Jump` | Star Jump | quadriceps | músculo: shoulders |
| `Step-up_with_Knee_Raise` | Step-up with Knee Raise | glutes | patrón: raise |
| `Stiff-Legged_Barbell_Deadlift` | Stiff-Legged Barbell Deadlift | hamstrings | patrón: deadlift |
| `Stiff-Legged_Dumbbell_Deadlift` | Stiff-Legged Dumbbell Deadlift | hamstrings | patrón: deadlift |
| `Stiff_Leg_Barbell_Good_Morning` | Stiff Leg Barbell Good Morning | lower back | patrón: good morning |
| `Straight-Arm_Dumbbell_Pullover` | Straight-Arm Dumbbell Pullover | chest | músculo: chest; músculo: lats; músculo: shoulders; patrón: pullover |
| `Straight-Arm_Pulldown` | Straight-Arm Pulldown | lats | músculo: lats; patrón: pulldown |
| `Straight_Bar_Bench_Mid_Rows` | Straight Bar Bench Mid Rows | middle back | músculo: middle back; músculo: lats; patrón: row |
| `Straight_Raises_on_Incline_Bench` | Straight Raises on Incline Bench | shoulders | músculo: shoulders; músculo: traps; patrón: raise |
| `Stride_Jump_Crossover` | Stride Jump Crossover | quadriceps | patrón: crossover |
| `Sumo_Deadlift` | Sumo Deadlift | hamstrings | músculo: middle back; músculo: traps; patrón: deadlift |
| `Sumo_Deadlift_with_Bands` | Sumo Deadlift with Bands | hamstrings | músculo: middle back; músculo: traps; patrón: deadlift |
| `Sumo_Deadlift_with_Chains` | Sumo Deadlift with Chains | hamstrings | músculo: middle back; músculo: traps; patrón: deadlift |
| `Supine_Chest_Throw` | Supine Chest Throw | triceps | músculo: chest; músculo: shoulders; patrón: row; patrón: throw |
| `Supine_One-Arm_Overhead_Throw` | Supine One-Arm Overhead Throw | abdominals | músculo: chest; músculo: lats; músculo: shoulders; patrón: overhead; patrón: row; patrón: throw |
| `Supine_Two-Arm_Overhead_Throw` | Supine Two-Arm Overhead Throw | abdominals | músculo: chest; músculo: lats; músculo: shoulders; patrón: overhead; patrón: row; patrón: throw |
| `Suspended_Fallout` | Suspended Fallout | abdominals | músculo: chest; músculo: shoulders |
| `Suspended_Push-Up` | Suspended Push-Up | chest | músculo: chest; músculo: shoulders; patrón: push up; patrón: pushup |
| `Suspended_Row` | Suspended Row | middle back | músculo: middle back; músculo: lats; patrón: row |
| `Suspended_Split_Squat` | Suspended Split Squat | quadriceps | patrón: squat |
| `Svend_Press` | Svend Press | chest | músculo: chest; músculo: shoulders; patrón: svend |
| `T-Bar_Row_with_Handle` | T-Bar Row with Handle | middle back | músculo: middle back; músculo: lats; patrón: row |
| `Tate_Press` | Tate Press | triceps | músculo: chest; músculo: shoulders |
| `Tire_Flip` | Tire Flip | quadriceps | músculo: chest; músculo: shoulders; músculo: traps |
| `Torso_Rotation` | Torso Rotation | abdominals | patrón: rotation |
| `Trap_Bar_Deadlift` | Trap Bar Deadlift | quadriceps | patrón: deadlift |
| `Tricep_Dumbbell_Kickback` | Tricep Dumbbell Kickback | triceps | patrón: kickback |
| `Tricep_Side_Stretch` | Tricep Side Stretch | triceps | músculo: shoulders; patrón: tricep side stretch |
| `Triceps_Overhead_Extension_with_Rope` | Triceps Overhead Extension with Rope | triceps | patrón: overhead; patrón: rope |
| `Triceps_Pushdown_-_Rope_Attachment` | Triceps Pushdown - Rope Attachment | triceps | patrón: rope |
| `Triceps_Stretch` | Triceps Stretch | triceps | músculo: lats; patrón: triceps stretch |
| `Two-Arm_Kettlebell_Clean` | Two-Arm Kettlebell Clean | shoulders | músculo: shoulders; músculo: traps; patrón: clean |
| `Two-Arm_Kettlebell_Jerk` | Two-Arm Kettlebell Jerk | shoulders | músculo: shoulders; patrón: jerk |
| `Two-Arm_Kettlebell_Military_Press` | Two-Arm Kettlebell Military Press | shoulders | músculo: shoulders; patrón: military |
| `Two-Arm_Kettlebell_Row` | Two-Arm Kettlebell Row | middle back | músculo: middle back; músculo: lats; patrón: row |
| `Underhand_Cable_Pulldowns` | Underhand Cable Pulldowns | lats | músculo: lats; músculo: middle back; músculo: shoulders; patrón: pulldown |
| `Upper_Back-Leg_Grab` | Upper Back-Leg Grab | hamstrings | músculo: middle back |
| `Upper_Back_Stretch` | Upper Back Stretch | middle back | músculo: middle back |
| `Upright_Barbell_Row` | Upright Barbell Row | shoulders | músculo: shoulders; músculo: traps; patrón: row |
| `Upright_Cable_Row` | Upright Cable Row | traps | músculo: traps; músculo: shoulders; patrón: row |
| `Upright_Row_-_With_Bands` | Upright Row - With Bands | traps | músculo: traps; músculo: shoulders; patrón: upright row; patrón: row |
| `Upward_Stretch` | Upward Stretch | shoulders | músculo: shoulders; músculo: chest; músculo: lats |
| `V-Bar_Pulldown` | V-Bar Pulldown | lats | músculo: lats; músculo: middle back; músculo: shoulders; patrón: pulldown |
| `V-Bar_Pullup` | V-Bar Pullup | lats | músculo: lats; músculo: middle back; músculo: shoulders; patrón: pull up; patrón: pullup |
| `Vertical_Swing` | Vertical Swing | hamstrings | músculo: shoulders; patrón: swing |
| `Weighted_Ball_Hyperextension` | Weighted Ball Hyperextension | lower back | músculo: middle back |
| `Weighted_Bench_Dip` | Weighted Bench Dip | triceps | músculo: chest; músculo: shoulders; patrón: dip |
| `Weighted_Jump_Squat` | Weighted Jump Squat | quadriceps | patrón: squat |
| `Weighted_Pull_Ups` | Weighted Pull Ups | lats | músculo: lats; músculo: middle back; patrón: pull up; patrón: pullup |
| `Weighted_Sissy_Squat` | Weighted Sissy Squat | quadriceps | patrón: squat |
| `Weighted_Squat` | Weighted Squat | quadriceps | patrón: squat |
| `Wide-Grip_Barbell_Bench_Press` | Wide-Grip Barbell Bench Press | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Wide-Grip_Decline_Barbell_Bench_Press` | Wide-Grip Decline Barbell Bench Press | chest | músculo: chest; músculo: shoulders; patrón: bench press |
| `Wide-Grip_Decline_Barbell_Pullover` | Wide-Grip Decline Barbell Pullover | chest | músculo: chest; músculo: shoulders; patrón: pullover |
| `Wide-Grip_Lat_Pulldown` | Wide-Grip Lat Pulldown | lats | músculo: lats; músculo: middle back; músculo: shoulders; patrón: pulldown |
| `Wide-Grip_Pulldown_Behind_The_Neck` | Wide-Grip Pulldown Behind The Neck | lats | músculo: lats; músculo: middle back; músculo: shoulders; patrón: behind the neck; patrón: pulldown |
| `Wide-Grip_Rear_Pull-Up` | Wide-Grip Rear Pull-Up | lats | músculo: lats; músculo: middle back; músculo: shoulders; patrón: pull up; patrón: pullup |
| `Wide_Stance_Barbell_Squat` | Wide Stance Barbell Squat | quadriceps | patrón: squat |
| `Wind_Sprints` | Wind Sprints | abdominals | patrón: wind sprint |
| `Windmills` | Windmills | abductors | patrón: windmill |
| `Wrist_Circles` | Wrist Circles | forearms | patrón: circles |
| `Wrist_Roller` | Wrist Roller | forearms | músculo: shoulders |
| `Wrist_Rotations_with_Straight_Bar` | Wrist Rotations with Straight Bar | forearms | patrón: rotation |
| `Yoke_Walk` | Yoke Walk | quadriceps | patrón: yoke |
| `Zercher_Squats` | Zercher Squats | quadriceps | patrón: squat |

## `rodilla_derecha` (406 bloqueados)

- Músculos: abductors, adductors, calves, glutes, hamstrings, quadriceps
- Patrones: `squat`, `lunge`, `jump`, `leg extension`, `leg press`, `leg curl`, `step up`, `stepup`, `pistol`, `split`, `hack`, `sissy`, `box`, `hops`, `bound`, `leap`, `hurdle`, `skip`, `sprint`, `running`, `jog`, `walk`, `carioca`, `shuffle`, `skating`, `cone`, `agility`, `mountain climber`, `burpee`, `kneeling`, `knee`, `rollout`, `ab roller`, `fallout`, `child's pose`, `cat stretch`, `all fours`, `crawl`, `groiner`, `stance`, `wall sit`, `clean`, `snatch`, `jerk`, `thruster`, `deadlift`, `sled`, `tire flip`, `yoke`, `farmer`, `stair`, `step mill`, `bicycl`, `bike`, `elliptical`, `treadmill`, `rowing`, `frog`, `rocket`, `tuck`, `throw`, `landmine`, `wood chop`, `woodchop`, `judo flip`, `battling`, `heavy bag`, `chest push`, `quad`, `hamstring`
- Ids extra: (ninguno)

| Id | Nombre | Músculo primario | Motivo |
|---|---|---|---|
| `90_90_Hamstring` | 90/90 Hamstring | hamstrings | músculo: hamstrings; músculo: calves; patrón: hamstring |
| `Ab_Roller` | Ab Roller | abdominals | patrón: ab roller |
| `Adductor` | Adductor | adductors | músculo: adductors |
| `Adductor_Groin` | Adductor/Groin | adductors | músculo: adductors |
| `Advanced_Kettlebell_Windmill` | Advanced Kettlebell Windmill | abdominals | músculo: glutes; músculo: hamstrings |
| `Air_Bike` | Air Bike | abdominals | patrón: bike |
| `All_Fours_Quad_Stretch` | All Fours Quad Stretch | quadriceps | músculo: quadriceps; patrón: all fours; patrón: quad |
| `Alternate_Leg_Diagonal_Bound` | Alternate Leg Diagonal Bound | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: bound |
| `Alternating_Hang_Clean` | Alternating Hang Clean | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; patrón: clean |
| `Ankle_Circles` | Ankle Circles | calves | músculo: calves |
| `Ankle_On_The_Knee` | Ankle On The Knee | glutes | músculo: glutes; patrón: knee |
| `Anterior_Tibialis-SMR` | Anterior Tibialis-SMR | calves | músculo: calves |
| `Atlas_Stone_Trainer` | Atlas Stone Trainer | lower back | músculo: glutes; músculo: hamstrings; músculo: quadriceps |
| `Atlas_Stones` | Atlas Stones | lower back | músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; músculo: quadriceps |
| `Axle_Deadlift` | Axle Deadlift | lower back | músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: deadlift |
| `Backward_Drag` | Backward Drag | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings |
| `Backward_Medicine_Ball_Throw` | Backward Medicine Ball Throw | shoulders | patrón: throw |
| `Balance_Board` | Balance Board | calves | músculo: calves; músculo: hamstrings; músculo: quadriceps |
| `Ball_Leg_Curl` | Ball Leg Curl | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; patrón: leg curl |
| `Band_Good_Morning` | Band Good Morning | hamstrings | músculo: hamstrings; músculo: glutes |
| `Band_Good_Morning_Pull_Through` | Band Good Morning (Pull Through) | hamstrings | músculo: hamstrings; músculo: glutes |
| `Band_Hip_Adductions` | Band Hip Adductions | adductors | músculo: adductors |
| `Barbell_Ab_Rollout` | Barbell Ab Rollout | abdominals | patrón: rollout |
| `Barbell_Ab_Rollout_-_On_Knees` | Barbell Ab Rollout - On Knees | abdominals | patrón: knee; patrón: rollout |
| `Barbell_Deadlift` | Barbell Deadlift | lower back | músculo: calves; músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: deadlift |
| `Barbell_Full_Squat` | Barbell Full Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Barbell_Glute_Bridge` | Barbell Glute Bridge | glutes | músculo: glutes; músculo: calves; músculo: hamstrings |
| `Barbell_Hack_Squat` | Barbell Hack Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: hamstrings; patrón: squat; patrón: hack |
| `Barbell_Hip_Thrust` | Barbell Hip Thrust | glutes | músculo: glutes; músculo: calves; músculo: hamstrings |
| `Barbell_Lunge` | Barbell Lunge | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: lunge |
| `Barbell_Rollout_from_Bench` | Barbell Rollout from Bench | abdominals | músculo: glutes; músculo: hamstrings; patrón: rollout |
| `Barbell_Seated_Calf_Raise` | Barbell Seated Calf Raise | calves | músculo: calves |
| `Barbell_Side_Split_Squat` | Barbell Side Split Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: hamstrings; patrón: squat; patrón: split |
| `Barbell_Squat` | Barbell Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Barbell_Squat_To_A_Bench` | Barbell Squat To A Bench | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Barbell_Step_Ups` | Barbell Step Ups | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: step up; patrón: stepup |
| `Barbell_Walking_Lunge` | Barbell Walking Lunge | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: lunge; patrón: walk |
| `Battling_Ropes` | Battling Ropes | shoulders | patrón: battling |
| `Bear_Crawl_Sled_Drags` | Bear Crawl Sled Drags | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: crawl; patrón: sled |
| `Bench_Jump` | Bench Jump | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: jump |
| `Bench_Sprint` | Bench Sprint | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: sprint |
| `Bent-Knee_Hip_Raise` | Bent-Knee Hip Raise | abdominals | patrón: knee |
| `Bent_Press` | Bent Press | abdominals | músculo: glutes; músculo: hamstrings; músculo: quadriceps |
| `Bicycling` | Bicycling | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: bicycl |
| `Bicycling_Stationary` | Bicycling, Stationary | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: bicycl |
| `Bodyweight_Squat` | Bodyweight Squat | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Bodyweight_Walking_Lunge` | Bodyweight Walking Lunge | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: lunge; patrón: walk |
| `Bottoms-Up_Clean_From_The_Hang_Position` | Bottoms-Up Clean From The Hang Position | forearms | patrón: clean |
| `Box_Jump_Multiple_Response` | Box Jump (Multiple Response) | hamstrings | músculo: hamstrings; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: jump; patrón: box |
| `Box_Skip` | Box Skip | hamstrings | músculo: hamstrings; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: box; patrón: skip |
| `Box_Squat` | Box Squat | quadriceps | músculo: quadriceps; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: box |
| `Box_Squat_with_Bands` | Box Squat with Bands | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: box |
| `Box_Squat_with_Chains` | Box Squat with Chains | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: box |
| `Butt_Lift_Bridge` | Butt Lift (Bridge) | glutes | músculo: glutes; músculo: hamstrings |
| `Cable_Deadlifts` | Cable Deadlifts | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: deadlift |
| `Cable_Hip_Adduction` | Cable Hip Adduction | quadriceps | músculo: quadriceps |
| `Cable_Judo_Flip` | Cable Judo Flip | abdominals | patrón: judo flip |
| `Calf_Press` | Calf Press | calves | músculo: calves |
| `Calf_Press_On_The_Leg_Press_Machine` | Calf Press On The Leg Press Machine | calves | músculo: calves; patrón: leg press |
| `Calf_Raise_On_A_Dumbbell` | Calf Raise On A Dumbbell | calves | músculo: calves |
| `Calf_Raises_-_With_Bands` | Calf Raises - With Bands | calves | músculo: calves |
| `Calf_Stretch_Elbows_Against_Wall` | Calf Stretch Elbows Against Wall | calves | músculo: calves |
| `Calf_Stretch_Hands_Against_Wall` | Calf Stretch Hands Against Wall | calves | músculo: calves |
| `Calves-SMR` | Calves-SMR | calves | músculo: calves |
| `Car_Deadlift` | Car Deadlift | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: deadlift |
| `Carioca_Quick_Step` | Carioca Quick Step | adductors | músculo: adductors; músculo: abductors; músculo: calves; músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: carioca |
| `Cat_Stretch` | Cat Stretch | lower back | patrón: cat stretch |
| `Catch_and_Overhead_Throw` | Catch and Overhead Throw | lats | patrón: throw |
| `Chair_Leg_Extended_Stretch` | Chair Leg Extended Stretch | hamstrings | músculo: hamstrings; músculo: adductors |
| `Chair_Squat` | Chair Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Chest_Push_from_3_point_stance` | Chest Push from 3 point stance | chest | patrón: stance; patrón: chest push |
| `Chest_Push_multiple_response` | Chest Push (multiple response) | chest | patrón: chest push |
| `Chest_Push_single_response` | Chest Push (single response) | chest | patrón: chest push |
| `Chest_Push_with_Run_Release` | Chest Push with Run Release | chest | patrón: chest push |
| `Childs_Pose` | Child's Pose | lower back | músculo: glutes; patrón: child's pose |
| `Circus_Bell` | Circus Bell | shoulders | músculo: glutes; músculo: hamstrings |
| `Clean` | Clean | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: clean |
| `Clean_Deadlift` | Clean Deadlift | hamstrings | músculo: hamstrings; músculo: glutes; músculo: quadriceps; patrón: clean; patrón: deadlift |
| `Clean_Pull` | Clean Pull | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: clean |
| `Clean_Shrug` | Clean Shrug | traps | patrón: clean |
| `Clean_and_Jerk` | Clean and Jerk | shoulders | músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: clean; patrón: jerk |
| `Clean_and_Press` | Clean and Press | shoulders | músculo: calves; músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: clean |
| `Clean_from_Blocks` | Clean from Blocks | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: clean |
| `Conans_Wheel` | Conan's Wheel | quadriceps | músculo: quadriceps; músculo: calves |
| `Crossover_Reverse_Lunge` | Crossover Reverse Lunge | lower back | músculo: abductors; músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: lunge |
| `Dancers_Stretch` | Dancer's Stretch | lower back | músculo: abductors; músculo: glutes |
| `Deadlift_with_Bands` | Deadlift with Bands | lower back | músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: deadlift |
| `Deadlift_with_Chains` | Deadlift with Chains | lower back | músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: deadlift |
| `Deficit_Deadlift` | Deficit Deadlift | lower back | músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: deadlift |
| `Depth_Jump_Leap` | Depth Jump Leap | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: jump; patrón: leap |
| `Donkey_Calf_Raises` | Donkey Calf Raises | calves | músculo: calves |
| `Double_Kettlebell_Alternating_Hang_Clean` | Double Kettlebell Alternating Hang Clean | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: clean |
| `Double_Kettlebell_Jerk` | Double Kettlebell Jerk | shoulders | músculo: calves; músculo: quadriceps; patrón: jerk |
| `Double_Kettlebell_Push_Press` | Double Kettlebell Push Press | shoulders | músculo: calves; músculo: quadriceps |
| `Double_Kettlebell_Snatch` | Double Kettlebell Snatch | shoulders | músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: snatch |
| `Double_Kettlebell_Windmill` | Double Kettlebell Windmill | abdominals | músculo: glutes; músculo: hamstrings |
| `Double_Leg_Butt_Kick` | Double Leg Butt Kick | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings |
| `Downward_Facing_Balance` | Downward Facing Balance | glutes | músculo: glutes; músculo: hamstrings |
| `Dumbbell_Clean` | Dumbbell Clean | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: clean |
| `Dumbbell_Lunges` | Dumbbell Lunges | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: lunge |
| `Dumbbell_Rear_Lunge` | Dumbbell Rear Lunge | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: lunge |
| `Dumbbell_Seated_Box_Jump` | Dumbbell Seated Box Jump | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: jump; patrón: box |
| `Dumbbell_Seated_One-Leg_Calf_Raise` | Dumbbell Seated One-Leg Calf Raise | calves | músculo: calves |
| `Dumbbell_Squat` | Dumbbell Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Dumbbell_Squat_To_A_Bench` | Dumbbell Squat To A Bench | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Dumbbell_Step_Ups` | Dumbbell Step Ups | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: step up; patrón: stepup |
| `Elbow_to_Knee` | Elbow to Knee | abdominals | patrón: knee |
| `Elevated_Back_Lunge` | Elevated Back Lunge | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: lunge |
| `Elliptical_Trainer` | Elliptical Trainer | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: elliptical |
| `Farmers_Walk` | Farmer's Walk | forearms | músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: walk; patrón: farmer |
| `Fast_Skipping` | Fast Skipping | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: skip |
| `Floor_Glute-Ham_Raise` | Floor Glute-Ham Raise | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes |
| `Flutter_Kicks` | Flutter Kicks | glutes | músculo: glutes; músculo: hamstrings |
| `Foot-SMR` | Foot-SMR | calves | músculo: calves |
| `Forward_Drag_with_Press` | Forward Drag with Press | chest | músculo: calves; músculo: glutes; músculo: hamstrings; músculo: quadriceps |
| `Frankenstein_Squat` | Frankenstein Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Freehand_Jump_Squat` | Freehand Jump Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: jump |
| `Frog_Hops` | Frog Hops | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: hops; patrón: frog |
| `Frog_Sit-Ups` | Frog Sit-Ups | abdominals | patrón: frog |
| `Front_Barbell_Squat` | Front Barbell Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Front_Barbell_Squat_To_A_Bench` | Front Barbell Squat To A Bench | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Front_Box_Jump` | Front Box Jump | hamstrings | músculo: hamstrings; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: jump; patrón: box |
| `Front_Cone_Hops_or_hurdle_hops` | Front Cone Hops (or hurdle hops) | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: hops; patrón: hurdle; patrón: cone |
| `Front_Leg_Raises` | Front Leg Raises | hamstrings | músculo: hamstrings |
| `Front_Squat_Clean_Grip` | Front Squat (Clean Grip) | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: clean |
| `Front_Squats_With_Two_Kettlebells` | Front Squats With Two Kettlebells | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; patrón: squat |
| `Glute_Ham_Raise` | Glute Ham Raise | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes |
| `Glute_Kickback` | Glute Kickback | glutes | músculo: glutes; músculo: hamstrings |
| `Goblet_Squat` | Goblet Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Good_Morning` | Good Morning | hamstrings | músculo: hamstrings; músculo: glutes |
| `Good_Morning_off_Pins` | Good Morning off Pins | hamstrings | músculo: hamstrings; músculo: glutes |
| `Groin_and_Back_Stretch` | Groin and Back Stretch | adductors | músculo: adductors |
| `Groiners` | Groiners | adductors | músculo: adductors; patrón: groiner |
| `Hack_Squat` | Hack Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: hack |
| `Hamstring-SMR` | Hamstring-SMR | hamstrings | músculo: hamstrings; patrón: hamstring |
| `Hamstring_Stretch` | Hamstring Stretch | hamstrings | músculo: hamstrings; patrón: hamstring |
| `Hang_Clean` | Hang Clean | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: clean |
| `Hang_Clean_-_Below_the_Knees` | Hang Clean - Below the Knees | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: knee; patrón: clean |
| `Hang_Snatch` | Hang Snatch | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: snatch |
| `Hang_Snatch_-_Below_Knees` | Hang Snatch - Below Knees | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: knee; patrón: snatch |
| `Hanging_Bar_Good_Morning` | Hanging Bar Good Morning | hamstrings | músculo: hamstrings; músculo: glutes |
| `Heaving_Snatch_Balance` | Heaving Snatch Balance | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: snatch |
| `Heavy_Bag_Thrust` | Heavy Bag Thrust | chest | patrón: heavy bag |
| `Hip_Circles_prone` | Hip Circles (prone) | abductors | músculo: abductors; músculo: adductors |
| `Hip_Extension_with_Bands` | Hip Extension with Bands | glutes | músculo: glutes; músculo: hamstrings |
| `Hip_Flexion_with_Band` | Hip Flexion with Band | quadriceps | músculo: quadriceps |
| `Hip_Lift_with_Band` | Hip Lift with Band | glutes | músculo: glutes; músculo: calves; músculo: hamstrings |
| `Hug_A_Ball` | Hug A Ball | lower back | músculo: calves; músculo: glutes |
| `Hug_Knees_To_Chest` | Hug Knees To Chest | lower back | músculo: glutes; patrón: knee |
| `Hurdle_Hops` | Hurdle Hops | hamstrings | músculo: hamstrings; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; patrón: hops; patrón: hurdle |
| `Hyperextensions_Back_Extensions` | Hyperextensions (Back Extensions) | lower back | músculo: glutes; músculo: hamstrings |
| `Hyperextensions_With_No_Hyperextension_Bench` | Hyperextensions With No Hyperextension Bench | lower back | músculo: glutes; músculo: hamstrings |
| `IT_Band_and_Glute_Stretch` | IT Band and Glute Stretch | abductors | músculo: abductors |
| `Iliotibial_Tract-SMR` | Iliotibial Tract-SMR | abductors | músculo: abductors |
| `Inchworm` | Inchworm | hamstrings | músculo: hamstrings |
| `Incline_Push-Up_Depth_Jump` | Incline Push-Up Depth Jump | chest | patrón: jump |
| `Intermediate_Groin_Stretch` | Intermediate Groin Stretch | hamstrings | músculo: hamstrings |
| `Intermediate_Hip_Flexor_and_Quad_Stretch` | Intermediate Hip Flexor and Quad Stretch | quadriceps | músculo: quadriceps; patrón: quad |
| `Iron_Cross` | Iron Cross | shoulders | músculo: glutes; músculo: hamstrings; músculo: quadriceps |
| `Iron_Crosses_stretch` | Iron Crosses (stretch) | quadriceps | músculo: quadriceps |
| `Jefferson_Squats` | Jefferson Squats | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Jerk_Balance` | Jerk Balance | shoulders | músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: jerk |
| `Jerk_Dip_Squat` | Jerk Dip Squat | quadriceps | músculo: quadriceps; músculo: calves; patrón: squat; patrón: jerk |
| `Jogging_Treadmill` | Jogging, Treadmill | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: jog; patrón: treadmill |
| `Keg_Load` | Keg Load | lower back | músculo: calves; músculo: glutes; músculo: hamstrings; músculo: quadriceps |
| `Kettlebell_Dead_Clean` | Kettlebell Dead Clean | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: clean |
| `Kettlebell_Figure_8` | Kettlebell Figure 8 | abdominals | músculo: hamstrings |
| `Kettlebell_Hang_Clean` | Kettlebell Hang Clean | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; patrón: clean |
| `Kettlebell_One-Legged_Deadlift` | Kettlebell One-Legged Deadlift | hamstrings | músculo: hamstrings; músculo: glutes; patrón: deadlift |
| `Kettlebell_Pass_Between_The_Legs` | Kettlebell Pass Between The Legs | abdominals | músculo: glutes; músculo: hamstrings |
| `Kettlebell_Pistol_Squat` | Kettlebell Pistol Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: pistol |
| `Kettlebell_Sumo_High_Pull` | Kettlebell Sumo High Pull | traps | músculo: adductors; músculo: glutes; músculo: hamstrings; músculo: quadriceps |
| `Kettlebell_Thruster` | Kettlebell Thruster | shoulders | músculo: quadriceps; patrón: thruster |
| `Kettlebell_Turkish_Get-Up_Lunge_style` | Kettlebell Turkish Get-Up (Lunge style) | shoulders | músculo: hamstrings; músculo: quadriceps; patrón: lunge |
| `Kettlebell_Turkish_Get-Up_Squat_style` | Kettlebell Turkish Get-Up (Squat style) | shoulders | músculo: calves; músculo: hamstrings; músculo: quadriceps; patrón: squat |
| `Kettlebell_Windmill` | Kettlebell Windmill | abdominals | músculo: glutes; músculo: hamstrings |
| `Knee_Across_The_Body` | Knee Across The Body | glutes | músculo: glutes; músculo: abductors; patrón: knee |
| `Knee_Circles` | Knee Circles | calves | músculo: calves; músculo: hamstrings; músculo: quadriceps; patrón: knee |
| `Knee_Hip_Raise_On_Parallel_Bars` | Knee/Hip Raise On Parallel Bars | abdominals | patrón: knee |
| `Knee_Tuck_Jump` | Knee Tuck Jump | hamstrings | músculo: hamstrings; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: jump; patrón: knee; patrón: tuck |
| `Kneeling_Arm_Drill` | Kneeling Arm Drill | shoulders | patrón: kneeling; patrón: knee |
| `Kneeling_Cable_Crunch_With_Alternating_Oblique_Twists` | Kneeling Cable Crunch With Alternating Oblique Twists | abdominals | patrón: kneeling; patrón: knee |
| `Kneeling_Cable_Triceps_Extension` | Kneeling Cable Triceps Extension | triceps | patrón: kneeling; patrón: knee |
| `Kneeling_Forearm_Stretch` | Kneeling Forearm Stretch | forearms | patrón: kneeling; patrón: knee |
| `Kneeling_High_Pulley_Row` | Kneeling High Pulley Row | lats | patrón: kneeling; patrón: knee |
| `Kneeling_Hip_Flexor` | Kneeling Hip Flexor | quadriceps | músculo: quadriceps; patrón: kneeling; patrón: knee |
| `Kneeling_Jump_Squat` | Kneeling Jump Squat | glutes | músculo: glutes; músculo: calves; músculo: hamstrings; músculo: quadriceps; patrón: squat; patrón: jump; patrón: kneeling; patrón: knee |
| `Kneeling_Single-Arm_High_Pulley_Row` | Kneeling Single-Arm High Pulley Row | lats | patrón: kneeling; patrón: knee |
| `Kneeling_Squat` | Kneeling Squat | glutes | músculo: glutes; músculo: hamstrings; patrón: squat; patrón: kneeling; patrón: knee |
| `Landmine_180s` | Landmine 180's | abdominals | músculo: glutes; patrón: landmine |
| `Landmine_Linear_Jammer` | Landmine Linear Jammer | shoulders | músculo: calves; músculo: hamstrings; músculo: quadriceps; patrón: landmine |
| `Lateral_Bound` | Lateral Bound | adductors | músculo: adductors; músculo: abductors; músculo: calves; músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: bound |
| `Lateral_Box_Jump` | Lateral Box Jump | adductors | músculo: adductors; músculo: abductors; músculo: calves; músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: jump; patrón: box |
| `Lateral_Cone_Hops` | Lateral Cone Hops | adductors | músculo: adductors; músculo: abductors; músculo: calves; músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: hops; patrón: cone |
| `Leg-Up_Hamstring_Stretch` | Leg-Up Hamstring Stretch | hamstrings | músculo: hamstrings; patrón: hamstring |
| `Leg_Extensions` | Leg Extensions | quadriceps | músculo: quadriceps; patrón: leg extension |
| `Leg_Lift` | Leg Lift | glutes | músculo: glutes; músculo: hamstrings |
| `Leg_Press` | Leg Press | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: leg press |
| `Leverage_Deadlift` | Leverage Deadlift | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: deadlift |
| `Linear_3-Part_Start_Technique` | Linear 3-Part Start Technique | hamstrings | músculo: hamstrings; músculo: calves; músculo: quadriceps |
| `Linear_Acceleration_Wall_Drill` | Linear Acceleration Wall Drill | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps |
| `Linear_Depth_Jump` | Linear Depth Jump | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: jump |
| `Log_Lift` | Log Lift | shoulders | músculo: glutes; músculo: hamstrings; músculo: quadriceps |
| `Looking_At_Ceiling` | Looking At Ceiling | quadriceps | músculo: quadriceps |
| `Lunge_Pass_Through` | Lunge Pass Through | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: lunge |
| `Lunge_Sprint` | Lunge Sprint | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: lunge; patrón: sprint |
| `Lying_Bent_Leg_Groin` | Lying Bent Leg Groin | adductors | músculo: adductors |
| `Lying_Crossover` | Lying Crossover | abductors | músculo: abductors |
| `Lying_Face_Down_Plate_Neck_Resistance` | Lying Face Down Plate Neck Resistance | neck | patrón: stance |
| `Lying_Face_Up_Plate_Neck_Resistance` | Lying Face Up Plate Neck Resistance | neck | patrón: stance |
| `Lying_Glute` | Lying Glute | glutes | músculo: glutes; músculo: abductors |
| `Lying_Hamstring` | Lying Hamstring | hamstrings | músculo: hamstrings; músculo: calves; patrón: hamstring |
| `Lying_Leg_Curls` | Lying Leg Curls | hamstrings | músculo: hamstrings; patrón: leg curl |
| `Lying_Machine_Squat` | Lying Machine Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Lying_Prone_Quadriceps` | Lying Prone Quadriceps | quadriceps | músculo: quadriceps; patrón: quad |
| `Medicine_Ball_Scoop_Throw` | Medicine Ball Scoop Throw | shoulders | músculo: hamstrings; músculo: quadriceps; patrón: throw |
| `Monster_Walk` | Monster Walk | abductors | músculo: abductors; patrón: walk |
| `Mountain_Climbers` | Mountain Climbers | quadriceps | músculo: quadriceps; músculo: hamstrings; patrón: mountain climber |
| `Moving_Claw_Series` | Moving Claw Series | hamstrings | músculo: hamstrings; músculo: calves; músculo: quadriceps |
| `Muscle_Snatch` | Muscle Snatch | hamstrings | músculo: hamstrings; músculo: glutes; músculo: quadriceps; patrón: snatch |
| `Narrow_Stance_Hack_Squats` | Narrow Stance Hack Squats | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: hack; patrón: stance |
| `Narrow_Stance_Leg_Press` | Narrow Stance Leg Press | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: leg press; patrón: stance |
| `Narrow_Stance_Squats` | Narrow Stance Squats | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: stance |
| `Natural_Glute_Ham_Raise` | Natural Glute Ham Raise | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes |
| `Olympic_Squat` | Olympic Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `On-Your-Back_Quad_Stretch` | On-Your-Back Quad Stretch | quadriceps | músculo: quadriceps; patrón: quad |
| `On_Your_Side_Quad_Stretch` | On Your Side Quad Stretch | quadriceps | músculo: quadriceps; patrón: quad |
| `One-Arm_Kettlebell_Clean` | One-Arm Kettlebell Clean | hamstrings | músculo: hamstrings; músculo: glutes; patrón: clean |
| `One-Arm_Kettlebell_Clean_and_Jerk` | One-Arm Kettlebell Clean and Jerk | shoulders | patrón: clean; patrón: jerk |
| `One-Arm_Kettlebell_Jerk` | One-Arm Kettlebell Jerk | shoulders | músculo: calves; músculo: quadriceps; patrón: jerk |
| `One-Arm_Kettlebell_Push_Press` | One-Arm Kettlebell Push Press | shoulders | músculo: calves; músculo: quadriceps |
| `One-Arm_Kettlebell_Snatch` | One-Arm Kettlebell Snatch | shoulders | músculo: calves; músculo: glutes; músculo: hamstrings; patrón: snatch |
| `One-Arm_Kettlebell_Split_Jerk` | One-Arm Kettlebell Split Jerk | shoulders | músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: split; patrón: jerk |
| `One-Arm_Kettlebell_Split_Snatch` | One-Arm Kettlebell Split Snatch | shoulders | músculo: hamstrings; músculo: quadriceps; patrón: split; patrón: snatch |
| `One-Arm_Kettlebell_Swings` | One-Arm Kettlebell Swings | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes |
| `One-Arm_Open_Palm_Kettlebell_Clean` | One-Arm Open Palm Kettlebell Clean | hamstrings | músculo: hamstrings; músculo: glutes; músculo: quadriceps; patrón: clean |
| `One-Arm_Overhead_Kettlebell_Squats` | One-Arm Overhead Kettlebell Squats | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `One-Arm_Side_Deadlift` | One-Arm Side Deadlift | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: deadlift |
| `One-Legged_Cable_Kickback` | One-Legged Cable Kickback | glutes | músculo: glutes; músculo: hamstrings |
| `One_Half_Locust` | One Half Locust | quadriceps | músculo: quadriceps |
| `One_Knee_To_Chest` | One Knee To Chest | glutes | músculo: glutes; músculo: hamstrings; patrón: knee |
| `One_Leg_Barbell_Squat` | One Leg Barbell Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Open_Palm_Kettlebell_Clean` | Open Palm Kettlebell Clean | hamstrings | músculo: hamstrings; músculo: glutes; músculo: quadriceps; patrón: clean |
| `Overhead_Squat` | Overhead Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Peroneals-SMR` | Peroneals-SMR | calves | músculo: calves |
| `Peroneals_Stretch` | Peroneals Stretch | calves | músculo: calves |
| `Physioball_Hip_Bridge` | Physioball Hip Bridge | glutes | músculo: glutes; músculo: hamstrings |
| `Piriformis-SMR` | Piriformis-SMR | glutes | músculo: glutes |
| `Platform_Hamstring_Slides` | Platform Hamstring Slides | hamstrings | músculo: hamstrings; músculo: glutes; patrón: hamstring |
| `Plie_Dumbbell_Squat` | Plie Dumbbell Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Plyo_Kettlebell_Pushups` | Plyo Kettlebell Pushups | chest | patrón: yoke |
| `Posterior_Tibialis_Stretch` | Posterior Tibialis Stretch | calves | músculo: calves |
| `Power_Clean` | Power Clean | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: clean |
| `Power_Clean_from_Blocks` | Power Clean from Blocks | hamstrings | músculo: hamstrings; músculo: quadriceps; patrón: clean |
| `Power_Jerk` | Power Jerk | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: jerk |
| `Power_Snatch` | Power Snatch | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: snatch |
| `Power_Snatch_from_Blocks` | Power Snatch from Blocks | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: snatch |
| `Power_Stairs` | Power Stairs | hamstrings | músculo: hamstrings; músculo: adductors; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: stair |
| `Prone_Manual_Hamstring` | Prone Manual Hamstring | hamstrings | músculo: hamstrings; patrón: hamstring |
| `Prowler_Sprint` | Prowler Sprint | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: sprint |
| `Pull_Through` | Pull Through | glutes | músculo: glutes; músculo: hamstrings |
| `Push_Press` | Push Press | shoulders | músculo: quadriceps |
| `Push_Press_-_Behind_the_Neck` | Push Press - Behind the Neck | shoulders | músculo: calves; músculo: quadriceps |
| `Quad_Stretch` | Quad Stretch | quadriceps | músculo: quadriceps; patrón: quad |
| `Quadriceps-SMR` | Quadriceps-SMR | quadriceps | músculo: quadriceps; patrón: quad |
| `Quick_Leap` | Quick Leap | quadriceps | músculo: quadriceps; músculo: calves; músculo: hamstrings; patrón: leap |
| `Rack_Pull_with_Bands` | Rack Pull with Bands | lower back | músculo: glutes; músculo: hamstrings; músculo: quadriceps |
| `Rack_Pulls` | Rack Pulls | lower back | músculo: glutes; músculo: hamstrings |
| `Rear_Leg_Raises` | Rear Leg Raises | quadriceps | músculo: quadriceps |
| `Recumbent_Bike` | Recumbent Bike | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: bike |
| `Return_Push_from_Stance` | Return Push from Stance | shoulders | patrón: stance |
| `Reverse_Band_Box_Squat` | Reverse Band Box Squat | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: box |
| `Reverse_Band_Deadlift` | Reverse Band Deadlift | lower back | músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: deadlift |
| `Reverse_Band_Power_Squat` | Reverse Band Power Squat | quadriceps | músculo: quadriceps; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Reverse_Band_Sumo_Deadlift` | Reverse Band Sumo Deadlift | hamstrings | músculo: hamstrings; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: deadlift |
| `Reverse_Hyperextension` | Reverse Hyperextension | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes |
| `Rickshaw_Carry` | Rickshaw Carry | forearms | músculo: calves; músculo: glutes; músculo: hamstrings; músculo: quadriceps |
| `Rickshaw_Deadlift` | Rickshaw Deadlift | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: deadlift |
| `Rocket_Jump` | Rocket Jump | quadriceps | músculo: quadriceps; músculo: calves; músculo: hamstrings; patrón: jump; patrón: rocket |
| `Rocking_Standing_Calf_Raise` | Rocking Standing Calf Raise | calves | músculo: calves |
| `Romanian_Deadlift` | Romanian Deadlift | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; patrón: deadlift |
| `Romanian_Deadlift_from_Deficit` | Romanian Deadlift from Deficit | hamstrings | músculo: hamstrings; músculo: glutes; patrón: deadlift |
| `Rope_Jumping` | Rope Jumping | quadriceps | músculo: quadriceps; músculo: calves; músculo: hamstrings; patrón: jump |
| `Rowing_Stationary` | Rowing, Stationary | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: rowing |
| `Runners_Stretch` | Runner's Stretch | hamstrings | músculo: hamstrings; músculo: calves |
| `Running_Treadmill` | Running, Treadmill | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: running; patrón: treadmill |
| `Sandbag_Load` | Sandbag Load | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings |
| `Scissors_Jump` | Scissors Jump | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: jump |
| `Seated_Band_Hamstring_Curl` | Seated Band Hamstring Curl | hamstrings | músculo: hamstrings; patrón: hamstring |
| `Seated_Calf_Raise` | Seated Calf Raise | calves | músculo: calves |
| `Seated_Calf_Stretch` | Seated Calf Stretch | calves | músculo: calves; músculo: hamstrings |
| `Seated_Floor_Hamstring_Stretch` | Seated Floor Hamstring Stretch | hamstrings | músculo: hamstrings; músculo: calves; patrón: hamstring |
| `Seated_Glute` | Seated Glute | glutes | músculo: glutes; músculo: adductors |
| `Seated_Good_Mornings` | Seated Good Mornings | lower back | músculo: glutes |
| `Seated_Hamstring` | Seated Hamstring | hamstrings | músculo: hamstrings; músculo: calves; patrón: hamstring |
| `Seated_Hamstring_and_Calf_Stretch` | Seated Hamstring and Calf Stretch | hamstrings | músculo: hamstrings; músculo: calves; patrón: hamstring |
| `Seated_Head_Harness_Neck_Resistance` | Seated Head Harness Neck Resistance | neck | patrón: stance |
| `Seated_Leg_Curl` | Seated Leg Curl | hamstrings | músculo: hamstrings; patrón: leg curl |
| `Seated_Leg_Tucks` | Seated Leg Tucks | abdominals | patrón: tuck |
| `Side_Hop-Sprint` | Side Hop-Sprint | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: hamstrings; patrón: hops; patrón: sprint |
| `Side_Leg_Raises` | Side Leg Raises | adductors | músculo: adductors |
| `Side_Lying_Groin_Stretch` | Side Lying Groin Stretch | adductors | músculo: adductors; músculo: hamstrings |
| `Side_Standing_Long_Jump` | Side Standing Long Jump | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: jump |
| `Side_to_Side_Box_Shuffle` | Side to Side Box Shuffle | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: hamstrings; patrón: box; patrón: shuffle |
| `Single-Cone_Sprint_Drill` | Single-Cone Sprint Drill | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: sprint; patrón: cone |
| `Single-Leg_High_Box_Squat` | Single-Leg High Box Squat | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: box |
| `Single-Leg_Hop_Progression` | Single-Leg Hop Progression | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: hamstrings |
| `Single-Leg_Lateral_Hop` | Single-Leg Lateral Hop | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: hamstrings |
| `Single-Leg_Leg_Extension` | Single-Leg Leg Extension | quadriceps | músculo: quadriceps; patrón: leg extension |
| `Single-Leg_Stride_Jump` | Single-Leg Stride Jump | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: hamstrings; patrón: jump |
| `Single_Leg_Butt_Kick` | Single Leg Butt Kick | quadriceps | músculo: quadriceps; músculo: calves; músculo: hamstrings |
| `Single_Leg_Glute_Bridge` | Single Leg Glute Bridge | glutes | músculo: glutes; músculo: hamstrings |
| `Single_Leg_Push-off` | Single Leg Push-off | quadriceps | músculo: quadriceps; músculo: calves; músculo: hamstrings |
| `Sit_Squats` | Sit Squats | quadriceps | músculo: quadriceps; músculo: abductors; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Skating` | Skating | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: skating |
| `Sled_Drag_-_Harness` | Sled Drag - Harness | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: sled |
| `Sled_Overhead_Backward_Walk` | Sled Overhead Backward Walk | shoulders | músculo: calves; músculo: quadriceps; patrón: walk; patrón: sled |
| `Sled_Overhead_Triceps_Extension` | Sled Overhead Triceps Extension | triceps | patrón: sled |
| `Sled_Push` | Sled Push | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: sled |
| `Sled_Reverse_Flye` | Sled Reverse Flye | shoulders | patrón: sled |
| `Sled_Row` | Sled Row | middle back | patrón: sled |
| `Sledgehammer_Swings` | Sledgehammer Swings | abdominals | músculo: calves; patrón: sled |
| `Smith_Machine_Calf_Raise` | Smith Machine Calf Raise | calves | músculo: calves |
| `Smith_Machine_Hang_Power_Clean` | Smith Machine Hang Power Clean | hamstrings | músculo: hamstrings; músculo: glutes; músculo: quadriceps; patrón: clean |
| `Smith_Machine_Leg_Press` | Smith Machine Leg Press | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: leg press |
| `Smith_Machine_Pistol_Squat` | Smith Machine Pistol Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: pistol |
| `Smith_Machine_Reverse_Calf_Raises` | Smith Machine Reverse Calf Raises | calves | músculo: calves |
| `Smith_Machine_Squat` | Smith Machine Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Smith_Machine_Stiff-Legged_Deadlift` | Smith Machine Stiff-Legged Deadlift | hamstrings | músculo: hamstrings; músculo: glutes; patrón: deadlift |
| `Smith_Single-Leg_Split_Squat` | Smith Single-Leg Split Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: split |
| `Snatch` | Snatch | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: snatch |
| `Snatch_Balance` | Snatch Balance | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: snatch |
| `Snatch_Deadlift` | Snatch Deadlift | hamstrings | músculo: hamstrings; músculo: glutes; músculo: quadriceps; patrón: snatch; patrón: deadlift |
| `Snatch_Pull` | Snatch Pull | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: snatch |
| `Snatch_Shrug` | Snatch Shrug | traps | patrón: snatch |
| `Snatch_from_Blocks` | Snatch from Blocks | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: snatch |
| `Speed_Box_Squat` | Speed Box Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: box |
| `Speed_Squats` | Speed Squats | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Spell_Caster` | Spell Caster | abdominals | músculo: glutes |
| `Spider_Crawl` | Spider Crawl | abdominals | patrón: crawl |
| `Split_Clean` | Split Clean | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: split; patrón: clean |
| `Split_Jerk` | Split Jerk | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: split; patrón: jerk |
| `Split_Jump` | Split Jump | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: jump; patrón: split |
| `Split_Snatch` | Split Snatch | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: split; patrón: snatch |
| `Split_Squat_with_Dumbbells` | Split Squat with Dumbbells | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: split |
| `Split_Squats` | Split Squats | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: squat; patrón: split |
| `Squat_Jerk` | Squat Jerk | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: jerk |
| `Squat_with_Bands` | Squat with Bands | quadriceps | músculo: quadriceps; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Squat_with_Chains` | Squat with Chains | quadriceps | músculo: quadriceps; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Squat_with_Plate_Movers` | Squat with Plate Movers | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Squats_-_With_Bands` | Squats - With Bands | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Stairmaster` | Stairmaster | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: stair |
| `Standing_Barbell_Calf_Raise` | Standing Barbell Calf Raise | calves | músculo: calves |
| `Standing_Cable_Wood_Chop` | Standing Cable Wood Chop | abdominals | patrón: wood chop; patrón: woodchop |
| `Standing_Calf_Raises` | Standing Calf Raises | calves | músculo: calves |
| `Standing_Dumbbell_Calf_Raise` | Standing Dumbbell Calf Raise | calves | músculo: calves |
| `Standing_Elevated_Quad_Stretch` | Standing Elevated Quad Stretch | quadriceps | músculo: quadriceps; patrón: quad |
| `Standing_Gastrocnemius_Calf_Stretch` | Standing Gastrocnemius Calf Stretch | calves | músculo: calves; músculo: hamstrings |
| `Standing_Hamstring_and_Calf_Stretch` | Standing Hamstring and Calf Stretch | hamstrings | músculo: hamstrings; patrón: hamstring |
| `Standing_Hip_Circles` | Standing Hip Circles | abductors | músculo: abductors; músculo: adductors |
| `Standing_Hip_Flexors` | Standing Hip Flexors | quadriceps | músculo: quadriceps |
| `Standing_Leg_Curl` | Standing Leg Curl | hamstrings | músculo: hamstrings; patrón: leg curl |
| `Standing_Long_Jump` | Standing Long Jump | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: jump |
| `Standing_Pelvic_Tilt` | Standing Pelvic Tilt | lower back | músculo: glutes |
| `Standing_Soleus_And_Achilles_Stretch` | Standing Soleus And Achilles Stretch | calves | músculo: calves |
| `Standing_Toe_Touches` | Standing Toe Touches | hamstrings | músculo: hamstrings; músculo: calves |
| `Standing_Two-Arm_Overhead_Throw` | Standing Two-Arm Overhead Throw | shoulders | patrón: throw |
| `Star_Jump` | Star Jump | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: jump |
| `Step-up_with_Knee_Raise` | Step-up with Knee Raise | glutes | músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: step up; patrón: stepup; patrón: knee |
| `Step_Mill` | Step Mill | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: step mill |
| `Stiff-Legged_Barbell_Deadlift` | Stiff-Legged Barbell Deadlift | hamstrings | músculo: hamstrings; músculo: glutes; patrón: deadlift |
| `Stiff-Legged_Dumbbell_Deadlift` | Stiff-Legged Dumbbell Deadlift | hamstrings | músculo: hamstrings; músculo: glutes; patrón: deadlift |
| `Stiff_Leg_Barbell_Good_Morning` | Stiff Leg Barbell Good Morning | lower back | músculo: glutes; músculo: hamstrings |
| `Stride_Jump_Crossover` | Stride Jump Crossover | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: hamstrings; patrón: jump |
| `Sumo_Deadlift` | Sumo Deadlift | hamstrings | músculo: hamstrings; músculo: adductors; músculo: glutes; músculo: quadriceps; patrón: deadlift |
| `Sumo_Deadlift_with_Bands` | Sumo Deadlift with Bands | hamstrings | músculo: hamstrings; músculo: adductors; músculo: glutes; músculo: quadriceps; patrón: deadlift |
| `Sumo_Deadlift_with_Chains` | Sumo Deadlift with Chains | hamstrings | músculo: hamstrings; músculo: abductors; músculo: adductors; músculo: glutes; músculo: quadriceps; patrón: deadlift |
| `Superman` | Superman | lower back | músculo: glutes; músculo: hamstrings |
| `Supine_Chest_Throw` | Supine Chest Throw | triceps | patrón: throw |
| `Supine_One-Arm_Overhead_Throw` | Supine One-Arm Overhead Throw | abdominals | patrón: throw |
| `Supine_Two-Arm_Overhead_Throw` | Supine Two-Arm Overhead Throw | abdominals | patrón: throw |
| `Suspended_Fallout` | Suspended Fallout | abdominals | patrón: fallout |
| `Suspended_Split_Squat` | Suspended Split Squat | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: split |
| `The_Straddle` | The Straddle | hamstrings | músculo: hamstrings; músculo: adductors; músculo: calves |
| `Thigh_Abductor` | Thigh Abductor | abductors | músculo: abductors; músculo: glutes |
| `Thigh_Adductor` | Thigh Adductor | adductors | músculo: adductors; músculo: glutes; músculo: hamstrings |
| `Tire_Flip` | Tire Flip | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: tire flip |
| `Trail_Running_Walking` | Trail Running/Walking | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: running; patrón: walk |
| `Trap_Bar_Deadlift` | Trap Bar Deadlift | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: deadlift |
| `Tuck_Crunch` | Tuck Crunch | abdominals | patrón: tuck |
| `Two-Arm_Kettlebell_Clean` | Two-Arm Kettlebell Clean | shoulders | músculo: calves; músculo: glutes; músculo: hamstrings; patrón: clean |
| `Two-Arm_Kettlebell_Jerk` | Two-Arm Kettlebell Jerk | shoulders | músculo: calves; músculo: quadriceps; patrón: jerk |
| `Upper_Back-Leg_Grab` | Upper Back-Leg Grab | hamstrings | músculo: hamstrings |
| `Vertical_Swing` | Vertical Swing | hamstrings | músculo: hamstrings; músculo: glutes; músculo: quadriceps |
| `Walking_Treadmill` | Walking, Treadmill | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: walk; patrón: treadmill |
| `Weighted_Ball_Hyperextension` | Weighted Ball Hyperextension | lower back | músculo: glutes; músculo: hamstrings |
| `Weighted_Jump_Squat` | Weighted Jump Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: jump |
| `Weighted_Sissy_Squat` | Weighted Sissy Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: sissy |
| `Weighted_Squat` | Weighted Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Wide_Stance_Barbell_Squat` | Wide Stance Barbell Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: stance |
| `Wide_Stance_Stiff_Legs` | Wide Stance Stiff Legs | hamstrings | músculo: hamstrings; músculo: adductors; músculo: glutes; patrón: stance |
| `Wind_Sprints` | Wind Sprints | abdominals | patrón: sprint |
| `Windmills` | Windmills | abductors | músculo: abductors; músculo: glutes; músculo: hamstrings |
| `Worlds_Greatest_Stretch` | World's Greatest Stretch | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps |
| `Yoke_Walk` | Yoke Walk | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: walk; patrón: yoke |
| `Zercher_Squats` | Zercher Squats | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |

## `rodilla_izquierda` (406 bloqueados)

- Músculos: abductors, adductors, calves, glutes, hamstrings, quadriceps
- Patrones: `squat`, `lunge`, `jump`, `leg extension`, `leg press`, `leg curl`, `step up`, `stepup`, `pistol`, `split`, `hack`, `sissy`, `box`, `hops`, `bound`, `leap`, `hurdle`, `skip`, `sprint`, `running`, `jog`, `walk`, `carioca`, `shuffle`, `skating`, `cone`, `agility`, `mountain climber`, `burpee`, `kneeling`, `knee`, `rollout`, `ab roller`, `fallout`, `child's pose`, `cat stretch`, `all fours`, `crawl`, `groiner`, `stance`, `wall sit`, `clean`, `snatch`, `jerk`, `thruster`, `deadlift`, `sled`, `tire flip`, `yoke`, `farmer`, `stair`, `step mill`, `bicycl`, `bike`, `elliptical`, `treadmill`, `rowing`, `frog`, `rocket`, `tuck`, `throw`, `landmine`, `wood chop`, `woodchop`, `judo flip`, `battling`, `heavy bag`, `chest push`, `quad`, `hamstring`
- Ids extra: (ninguno)

| Id | Nombre | Músculo primario | Motivo |
|---|---|---|---|
| `90_90_Hamstring` | 90/90 Hamstring | hamstrings | músculo: hamstrings; músculo: calves; patrón: hamstring |
| `Ab_Roller` | Ab Roller | abdominals | patrón: ab roller |
| `Adductor` | Adductor | adductors | músculo: adductors |
| `Adductor_Groin` | Adductor/Groin | adductors | músculo: adductors |
| `Advanced_Kettlebell_Windmill` | Advanced Kettlebell Windmill | abdominals | músculo: glutes; músculo: hamstrings |
| `Air_Bike` | Air Bike | abdominals | patrón: bike |
| `All_Fours_Quad_Stretch` | All Fours Quad Stretch | quadriceps | músculo: quadriceps; patrón: all fours; patrón: quad |
| `Alternate_Leg_Diagonal_Bound` | Alternate Leg Diagonal Bound | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: bound |
| `Alternating_Hang_Clean` | Alternating Hang Clean | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; patrón: clean |
| `Ankle_Circles` | Ankle Circles | calves | músculo: calves |
| `Ankle_On_The_Knee` | Ankle On The Knee | glutes | músculo: glutes; patrón: knee |
| `Anterior_Tibialis-SMR` | Anterior Tibialis-SMR | calves | músculo: calves |
| `Atlas_Stone_Trainer` | Atlas Stone Trainer | lower back | músculo: glutes; músculo: hamstrings; músculo: quadriceps |
| `Atlas_Stones` | Atlas Stones | lower back | músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; músculo: quadriceps |
| `Axle_Deadlift` | Axle Deadlift | lower back | músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: deadlift |
| `Backward_Drag` | Backward Drag | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings |
| `Backward_Medicine_Ball_Throw` | Backward Medicine Ball Throw | shoulders | patrón: throw |
| `Balance_Board` | Balance Board | calves | músculo: calves; músculo: hamstrings; músculo: quadriceps |
| `Ball_Leg_Curl` | Ball Leg Curl | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; patrón: leg curl |
| `Band_Good_Morning` | Band Good Morning | hamstrings | músculo: hamstrings; músculo: glutes |
| `Band_Good_Morning_Pull_Through` | Band Good Morning (Pull Through) | hamstrings | músculo: hamstrings; músculo: glutes |
| `Band_Hip_Adductions` | Band Hip Adductions | adductors | músculo: adductors |
| `Barbell_Ab_Rollout` | Barbell Ab Rollout | abdominals | patrón: rollout |
| `Barbell_Ab_Rollout_-_On_Knees` | Barbell Ab Rollout - On Knees | abdominals | patrón: knee; patrón: rollout |
| `Barbell_Deadlift` | Barbell Deadlift | lower back | músculo: calves; músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: deadlift |
| `Barbell_Full_Squat` | Barbell Full Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Barbell_Glute_Bridge` | Barbell Glute Bridge | glutes | músculo: glutes; músculo: calves; músculo: hamstrings |
| `Barbell_Hack_Squat` | Barbell Hack Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: hamstrings; patrón: squat; patrón: hack |
| `Barbell_Hip_Thrust` | Barbell Hip Thrust | glutes | músculo: glutes; músculo: calves; músculo: hamstrings |
| `Barbell_Lunge` | Barbell Lunge | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: lunge |
| `Barbell_Rollout_from_Bench` | Barbell Rollout from Bench | abdominals | músculo: glutes; músculo: hamstrings; patrón: rollout |
| `Barbell_Seated_Calf_Raise` | Barbell Seated Calf Raise | calves | músculo: calves |
| `Barbell_Side_Split_Squat` | Barbell Side Split Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: hamstrings; patrón: squat; patrón: split |
| `Barbell_Squat` | Barbell Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Barbell_Squat_To_A_Bench` | Barbell Squat To A Bench | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Barbell_Step_Ups` | Barbell Step Ups | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: step up; patrón: stepup |
| `Barbell_Walking_Lunge` | Barbell Walking Lunge | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: lunge; patrón: walk |
| `Battling_Ropes` | Battling Ropes | shoulders | patrón: battling |
| `Bear_Crawl_Sled_Drags` | Bear Crawl Sled Drags | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: crawl; patrón: sled |
| `Bench_Jump` | Bench Jump | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: jump |
| `Bench_Sprint` | Bench Sprint | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: sprint |
| `Bent-Knee_Hip_Raise` | Bent-Knee Hip Raise | abdominals | patrón: knee |
| `Bent_Press` | Bent Press | abdominals | músculo: glutes; músculo: hamstrings; músculo: quadriceps |
| `Bicycling` | Bicycling | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: bicycl |
| `Bicycling_Stationary` | Bicycling, Stationary | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: bicycl |
| `Bodyweight_Squat` | Bodyweight Squat | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Bodyweight_Walking_Lunge` | Bodyweight Walking Lunge | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: lunge; patrón: walk |
| `Bottoms-Up_Clean_From_The_Hang_Position` | Bottoms-Up Clean From The Hang Position | forearms | patrón: clean |
| `Box_Jump_Multiple_Response` | Box Jump (Multiple Response) | hamstrings | músculo: hamstrings; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: jump; patrón: box |
| `Box_Skip` | Box Skip | hamstrings | músculo: hamstrings; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: box; patrón: skip |
| `Box_Squat` | Box Squat | quadriceps | músculo: quadriceps; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: box |
| `Box_Squat_with_Bands` | Box Squat with Bands | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: box |
| `Box_Squat_with_Chains` | Box Squat with Chains | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: box |
| `Butt_Lift_Bridge` | Butt Lift (Bridge) | glutes | músculo: glutes; músculo: hamstrings |
| `Cable_Deadlifts` | Cable Deadlifts | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: deadlift |
| `Cable_Hip_Adduction` | Cable Hip Adduction | quadriceps | músculo: quadriceps |
| `Cable_Judo_Flip` | Cable Judo Flip | abdominals | patrón: judo flip |
| `Calf_Press` | Calf Press | calves | músculo: calves |
| `Calf_Press_On_The_Leg_Press_Machine` | Calf Press On The Leg Press Machine | calves | músculo: calves; patrón: leg press |
| `Calf_Raise_On_A_Dumbbell` | Calf Raise On A Dumbbell | calves | músculo: calves |
| `Calf_Raises_-_With_Bands` | Calf Raises - With Bands | calves | músculo: calves |
| `Calf_Stretch_Elbows_Against_Wall` | Calf Stretch Elbows Against Wall | calves | músculo: calves |
| `Calf_Stretch_Hands_Against_Wall` | Calf Stretch Hands Against Wall | calves | músculo: calves |
| `Calves-SMR` | Calves-SMR | calves | músculo: calves |
| `Car_Deadlift` | Car Deadlift | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: deadlift |
| `Carioca_Quick_Step` | Carioca Quick Step | adductors | músculo: adductors; músculo: abductors; músculo: calves; músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: carioca |
| `Cat_Stretch` | Cat Stretch | lower back | patrón: cat stretch |
| `Catch_and_Overhead_Throw` | Catch and Overhead Throw | lats | patrón: throw |
| `Chair_Leg_Extended_Stretch` | Chair Leg Extended Stretch | hamstrings | músculo: hamstrings; músculo: adductors |
| `Chair_Squat` | Chair Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Chest_Push_from_3_point_stance` | Chest Push from 3 point stance | chest | patrón: stance; patrón: chest push |
| `Chest_Push_multiple_response` | Chest Push (multiple response) | chest | patrón: chest push |
| `Chest_Push_single_response` | Chest Push (single response) | chest | patrón: chest push |
| `Chest_Push_with_Run_Release` | Chest Push with Run Release | chest | patrón: chest push |
| `Childs_Pose` | Child's Pose | lower back | músculo: glutes; patrón: child's pose |
| `Circus_Bell` | Circus Bell | shoulders | músculo: glutes; músculo: hamstrings |
| `Clean` | Clean | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: clean |
| `Clean_Deadlift` | Clean Deadlift | hamstrings | músculo: hamstrings; músculo: glutes; músculo: quadriceps; patrón: clean; patrón: deadlift |
| `Clean_Pull` | Clean Pull | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: clean |
| `Clean_Shrug` | Clean Shrug | traps | patrón: clean |
| `Clean_and_Jerk` | Clean and Jerk | shoulders | músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: clean; patrón: jerk |
| `Clean_and_Press` | Clean and Press | shoulders | músculo: calves; músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: clean |
| `Clean_from_Blocks` | Clean from Blocks | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: clean |
| `Conans_Wheel` | Conan's Wheel | quadriceps | músculo: quadriceps; músculo: calves |
| `Crossover_Reverse_Lunge` | Crossover Reverse Lunge | lower back | músculo: abductors; músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: lunge |
| `Dancers_Stretch` | Dancer's Stretch | lower back | músculo: abductors; músculo: glutes |
| `Deadlift_with_Bands` | Deadlift with Bands | lower back | músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: deadlift |
| `Deadlift_with_Chains` | Deadlift with Chains | lower back | músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: deadlift |
| `Deficit_Deadlift` | Deficit Deadlift | lower back | músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: deadlift |
| `Depth_Jump_Leap` | Depth Jump Leap | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: jump; patrón: leap |
| `Donkey_Calf_Raises` | Donkey Calf Raises | calves | músculo: calves |
| `Double_Kettlebell_Alternating_Hang_Clean` | Double Kettlebell Alternating Hang Clean | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: clean |
| `Double_Kettlebell_Jerk` | Double Kettlebell Jerk | shoulders | músculo: calves; músculo: quadriceps; patrón: jerk |
| `Double_Kettlebell_Push_Press` | Double Kettlebell Push Press | shoulders | músculo: calves; músculo: quadriceps |
| `Double_Kettlebell_Snatch` | Double Kettlebell Snatch | shoulders | músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: snatch |
| `Double_Kettlebell_Windmill` | Double Kettlebell Windmill | abdominals | músculo: glutes; músculo: hamstrings |
| `Double_Leg_Butt_Kick` | Double Leg Butt Kick | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings |
| `Downward_Facing_Balance` | Downward Facing Balance | glutes | músculo: glutes; músculo: hamstrings |
| `Dumbbell_Clean` | Dumbbell Clean | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: clean |
| `Dumbbell_Lunges` | Dumbbell Lunges | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: lunge |
| `Dumbbell_Rear_Lunge` | Dumbbell Rear Lunge | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: lunge |
| `Dumbbell_Seated_Box_Jump` | Dumbbell Seated Box Jump | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: jump; patrón: box |
| `Dumbbell_Seated_One-Leg_Calf_Raise` | Dumbbell Seated One-Leg Calf Raise | calves | músculo: calves |
| `Dumbbell_Squat` | Dumbbell Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Dumbbell_Squat_To_A_Bench` | Dumbbell Squat To A Bench | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Dumbbell_Step_Ups` | Dumbbell Step Ups | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: step up; patrón: stepup |
| `Elbow_to_Knee` | Elbow to Knee | abdominals | patrón: knee |
| `Elevated_Back_Lunge` | Elevated Back Lunge | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: lunge |
| `Elliptical_Trainer` | Elliptical Trainer | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: elliptical |
| `Farmers_Walk` | Farmer's Walk | forearms | músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: walk; patrón: farmer |
| `Fast_Skipping` | Fast Skipping | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: skip |
| `Floor_Glute-Ham_Raise` | Floor Glute-Ham Raise | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes |
| `Flutter_Kicks` | Flutter Kicks | glutes | músculo: glutes; músculo: hamstrings |
| `Foot-SMR` | Foot-SMR | calves | músculo: calves |
| `Forward_Drag_with_Press` | Forward Drag with Press | chest | músculo: calves; músculo: glutes; músculo: hamstrings; músculo: quadriceps |
| `Frankenstein_Squat` | Frankenstein Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Freehand_Jump_Squat` | Freehand Jump Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: jump |
| `Frog_Hops` | Frog Hops | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: hops; patrón: frog |
| `Frog_Sit-Ups` | Frog Sit-Ups | abdominals | patrón: frog |
| `Front_Barbell_Squat` | Front Barbell Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Front_Barbell_Squat_To_A_Bench` | Front Barbell Squat To A Bench | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Front_Box_Jump` | Front Box Jump | hamstrings | músculo: hamstrings; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: jump; patrón: box |
| `Front_Cone_Hops_or_hurdle_hops` | Front Cone Hops (or hurdle hops) | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: hops; patrón: hurdle; patrón: cone |
| `Front_Leg_Raises` | Front Leg Raises | hamstrings | músculo: hamstrings |
| `Front_Squat_Clean_Grip` | Front Squat (Clean Grip) | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: clean |
| `Front_Squats_With_Two_Kettlebells` | Front Squats With Two Kettlebells | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; patrón: squat |
| `Glute_Ham_Raise` | Glute Ham Raise | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes |
| `Glute_Kickback` | Glute Kickback | glutes | músculo: glutes; músculo: hamstrings |
| `Goblet_Squat` | Goblet Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Good_Morning` | Good Morning | hamstrings | músculo: hamstrings; músculo: glutes |
| `Good_Morning_off_Pins` | Good Morning off Pins | hamstrings | músculo: hamstrings; músculo: glutes |
| `Groin_and_Back_Stretch` | Groin and Back Stretch | adductors | músculo: adductors |
| `Groiners` | Groiners | adductors | músculo: adductors; patrón: groiner |
| `Hack_Squat` | Hack Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: hack |
| `Hamstring-SMR` | Hamstring-SMR | hamstrings | músculo: hamstrings; patrón: hamstring |
| `Hamstring_Stretch` | Hamstring Stretch | hamstrings | músculo: hamstrings; patrón: hamstring |
| `Hang_Clean` | Hang Clean | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: clean |
| `Hang_Clean_-_Below_the_Knees` | Hang Clean - Below the Knees | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: knee; patrón: clean |
| `Hang_Snatch` | Hang Snatch | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: snatch |
| `Hang_Snatch_-_Below_Knees` | Hang Snatch - Below Knees | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: knee; patrón: snatch |
| `Hanging_Bar_Good_Morning` | Hanging Bar Good Morning | hamstrings | músculo: hamstrings; músculo: glutes |
| `Heaving_Snatch_Balance` | Heaving Snatch Balance | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: snatch |
| `Heavy_Bag_Thrust` | Heavy Bag Thrust | chest | patrón: heavy bag |
| `Hip_Circles_prone` | Hip Circles (prone) | abductors | músculo: abductors; músculo: adductors |
| `Hip_Extension_with_Bands` | Hip Extension with Bands | glutes | músculo: glutes; músculo: hamstrings |
| `Hip_Flexion_with_Band` | Hip Flexion with Band | quadriceps | músculo: quadriceps |
| `Hip_Lift_with_Band` | Hip Lift with Band | glutes | músculo: glutes; músculo: calves; músculo: hamstrings |
| `Hug_A_Ball` | Hug A Ball | lower back | músculo: calves; músculo: glutes |
| `Hug_Knees_To_Chest` | Hug Knees To Chest | lower back | músculo: glutes; patrón: knee |
| `Hurdle_Hops` | Hurdle Hops | hamstrings | músculo: hamstrings; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; patrón: hops; patrón: hurdle |
| `Hyperextensions_Back_Extensions` | Hyperextensions (Back Extensions) | lower back | músculo: glutes; músculo: hamstrings |
| `Hyperextensions_With_No_Hyperextension_Bench` | Hyperextensions With No Hyperextension Bench | lower back | músculo: glutes; músculo: hamstrings |
| `IT_Band_and_Glute_Stretch` | IT Band and Glute Stretch | abductors | músculo: abductors |
| `Iliotibial_Tract-SMR` | Iliotibial Tract-SMR | abductors | músculo: abductors |
| `Inchworm` | Inchworm | hamstrings | músculo: hamstrings |
| `Incline_Push-Up_Depth_Jump` | Incline Push-Up Depth Jump | chest | patrón: jump |
| `Intermediate_Groin_Stretch` | Intermediate Groin Stretch | hamstrings | músculo: hamstrings |
| `Intermediate_Hip_Flexor_and_Quad_Stretch` | Intermediate Hip Flexor and Quad Stretch | quadriceps | músculo: quadriceps; patrón: quad |
| `Iron_Cross` | Iron Cross | shoulders | músculo: glutes; músculo: hamstrings; músculo: quadriceps |
| `Iron_Crosses_stretch` | Iron Crosses (stretch) | quadriceps | músculo: quadriceps |
| `Jefferson_Squats` | Jefferson Squats | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Jerk_Balance` | Jerk Balance | shoulders | músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: jerk |
| `Jerk_Dip_Squat` | Jerk Dip Squat | quadriceps | músculo: quadriceps; músculo: calves; patrón: squat; patrón: jerk |
| `Jogging_Treadmill` | Jogging, Treadmill | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: jog; patrón: treadmill |
| `Keg_Load` | Keg Load | lower back | músculo: calves; músculo: glutes; músculo: hamstrings; músculo: quadriceps |
| `Kettlebell_Dead_Clean` | Kettlebell Dead Clean | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: clean |
| `Kettlebell_Figure_8` | Kettlebell Figure 8 | abdominals | músculo: hamstrings |
| `Kettlebell_Hang_Clean` | Kettlebell Hang Clean | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; patrón: clean |
| `Kettlebell_One-Legged_Deadlift` | Kettlebell One-Legged Deadlift | hamstrings | músculo: hamstrings; músculo: glutes; patrón: deadlift |
| `Kettlebell_Pass_Between_The_Legs` | Kettlebell Pass Between The Legs | abdominals | músculo: glutes; músculo: hamstrings |
| `Kettlebell_Pistol_Squat` | Kettlebell Pistol Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: pistol |
| `Kettlebell_Sumo_High_Pull` | Kettlebell Sumo High Pull | traps | músculo: adductors; músculo: glutes; músculo: hamstrings; músculo: quadriceps |
| `Kettlebell_Thruster` | Kettlebell Thruster | shoulders | músculo: quadriceps; patrón: thruster |
| `Kettlebell_Turkish_Get-Up_Lunge_style` | Kettlebell Turkish Get-Up (Lunge style) | shoulders | músculo: hamstrings; músculo: quadriceps; patrón: lunge |
| `Kettlebell_Turkish_Get-Up_Squat_style` | Kettlebell Turkish Get-Up (Squat style) | shoulders | músculo: calves; músculo: hamstrings; músculo: quadriceps; patrón: squat |
| `Kettlebell_Windmill` | Kettlebell Windmill | abdominals | músculo: glutes; músculo: hamstrings |
| `Knee_Across_The_Body` | Knee Across The Body | glutes | músculo: glutes; músculo: abductors; patrón: knee |
| `Knee_Circles` | Knee Circles | calves | músculo: calves; músculo: hamstrings; músculo: quadriceps; patrón: knee |
| `Knee_Hip_Raise_On_Parallel_Bars` | Knee/Hip Raise On Parallel Bars | abdominals | patrón: knee |
| `Knee_Tuck_Jump` | Knee Tuck Jump | hamstrings | músculo: hamstrings; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: jump; patrón: knee; patrón: tuck |
| `Kneeling_Arm_Drill` | Kneeling Arm Drill | shoulders | patrón: kneeling; patrón: knee |
| `Kneeling_Cable_Crunch_With_Alternating_Oblique_Twists` | Kneeling Cable Crunch With Alternating Oblique Twists | abdominals | patrón: kneeling; patrón: knee |
| `Kneeling_Cable_Triceps_Extension` | Kneeling Cable Triceps Extension | triceps | patrón: kneeling; patrón: knee |
| `Kneeling_Forearm_Stretch` | Kneeling Forearm Stretch | forearms | patrón: kneeling; patrón: knee |
| `Kneeling_High_Pulley_Row` | Kneeling High Pulley Row | lats | patrón: kneeling; patrón: knee |
| `Kneeling_Hip_Flexor` | Kneeling Hip Flexor | quadriceps | músculo: quadriceps; patrón: kneeling; patrón: knee |
| `Kneeling_Jump_Squat` | Kneeling Jump Squat | glutes | músculo: glutes; músculo: calves; músculo: hamstrings; músculo: quadriceps; patrón: squat; patrón: jump; patrón: kneeling; patrón: knee |
| `Kneeling_Single-Arm_High_Pulley_Row` | Kneeling Single-Arm High Pulley Row | lats | patrón: kneeling; patrón: knee |
| `Kneeling_Squat` | Kneeling Squat | glutes | músculo: glutes; músculo: hamstrings; patrón: squat; patrón: kneeling; patrón: knee |
| `Landmine_180s` | Landmine 180's | abdominals | músculo: glutes; patrón: landmine |
| `Landmine_Linear_Jammer` | Landmine Linear Jammer | shoulders | músculo: calves; músculo: hamstrings; músculo: quadriceps; patrón: landmine |
| `Lateral_Bound` | Lateral Bound | adductors | músculo: adductors; músculo: abductors; músculo: calves; músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: bound |
| `Lateral_Box_Jump` | Lateral Box Jump | adductors | músculo: adductors; músculo: abductors; músculo: calves; músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: jump; patrón: box |
| `Lateral_Cone_Hops` | Lateral Cone Hops | adductors | músculo: adductors; músculo: abductors; músculo: calves; músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: hops; patrón: cone |
| `Leg-Up_Hamstring_Stretch` | Leg-Up Hamstring Stretch | hamstrings | músculo: hamstrings; patrón: hamstring |
| `Leg_Extensions` | Leg Extensions | quadriceps | músculo: quadriceps; patrón: leg extension |
| `Leg_Lift` | Leg Lift | glutes | músculo: glutes; músculo: hamstrings |
| `Leg_Press` | Leg Press | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: leg press |
| `Leverage_Deadlift` | Leverage Deadlift | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: deadlift |
| `Linear_3-Part_Start_Technique` | Linear 3-Part Start Technique | hamstrings | músculo: hamstrings; músculo: calves; músculo: quadriceps |
| `Linear_Acceleration_Wall_Drill` | Linear Acceleration Wall Drill | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps |
| `Linear_Depth_Jump` | Linear Depth Jump | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: jump |
| `Log_Lift` | Log Lift | shoulders | músculo: glutes; músculo: hamstrings; músculo: quadriceps |
| `Looking_At_Ceiling` | Looking At Ceiling | quadriceps | músculo: quadriceps |
| `Lunge_Pass_Through` | Lunge Pass Through | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: lunge |
| `Lunge_Sprint` | Lunge Sprint | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: lunge; patrón: sprint |
| `Lying_Bent_Leg_Groin` | Lying Bent Leg Groin | adductors | músculo: adductors |
| `Lying_Crossover` | Lying Crossover | abductors | músculo: abductors |
| `Lying_Face_Down_Plate_Neck_Resistance` | Lying Face Down Plate Neck Resistance | neck | patrón: stance |
| `Lying_Face_Up_Plate_Neck_Resistance` | Lying Face Up Plate Neck Resistance | neck | patrón: stance |
| `Lying_Glute` | Lying Glute | glutes | músculo: glutes; músculo: abductors |
| `Lying_Hamstring` | Lying Hamstring | hamstrings | músculo: hamstrings; músculo: calves; patrón: hamstring |
| `Lying_Leg_Curls` | Lying Leg Curls | hamstrings | músculo: hamstrings; patrón: leg curl |
| `Lying_Machine_Squat` | Lying Machine Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Lying_Prone_Quadriceps` | Lying Prone Quadriceps | quadriceps | músculo: quadriceps; patrón: quad |
| `Medicine_Ball_Scoop_Throw` | Medicine Ball Scoop Throw | shoulders | músculo: hamstrings; músculo: quadriceps; patrón: throw |
| `Monster_Walk` | Monster Walk | abductors | músculo: abductors; patrón: walk |
| `Mountain_Climbers` | Mountain Climbers | quadriceps | músculo: quadriceps; músculo: hamstrings; patrón: mountain climber |
| `Moving_Claw_Series` | Moving Claw Series | hamstrings | músculo: hamstrings; músculo: calves; músculo: quadriceps |
| `Muscle_Snatch` | Muscle Snatch | hamstrings | músculo: hamstrings; músculo: glutes; músculo: quadriceps; patrón: snatch |
| `Narrow_Stance_Hack_Squats` | Narrow Stance Hack Squats | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: hack; patrón: stance |
| `Narrow_Stance_Leg_Press` | Narrow Stance Leg Press | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: leg press; patrón: stance |
| `Narrow_Stance_Squats` | Narrow Stance Squats | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: stance |
| `Natural_Glute_Ham_Raise` | Natural Glute Ham Raise | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes |
| `Olympic_Squat` | Olympic Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `On-Your-Back_Quad_Stretch` | On-Your-Back Quad Stretch | quadriceps | músculo: quadriceps; patrón: quad |
| `On_Your_Side_Quad_Stretch` | On Your Side Quad Stretch | quadriceps | músculo: quadriceps; patrón: quad |
| `One-Arm_Kettlebell_Clean` | One-Arm Kettlebell Clean | hamstrings | músculo: hamstrings; músculo: glutes; patrón: clean |
| `One-Arm_Kettlebell_Clean_and_Jerk` | One-Arm Kettlebell Clean and Jerk | shoulders | patrón: clean; patrón: jerk |
| `One-Arm_Kettlebell_Jerk` | One-Arm Kettlebell Jerk | shoulders | músculo: calves; músculo: quadriceps; patrón: jerk |
| `One-Arm_Kettlebell_Push_Press` | One-Arm Kettlebell Push Press | shoulders | músculo: calves; músculo: quadriceps |
| `One-Arm_Kettlebell_Snatch` | One-Arm Kettlebell Snatch | shoulders | músculo: calves; músculo: glutes; músculo: hamstrings; patrón: snatch |
| `One-Arm_Kettlebell_Split_Jerk` | One-Arm Kettlebell Split Jerk | shoulders | músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: split; patrón: jerk |
| `One-Arm_Kettlebell_Split_Snatch` | One-Arm Kettlebell Split Snatch | shoulders | músculo: hamstrings; músculo: quadriceps; patrón: split; patrón: snatch |
| `One-Arm_Kettlebell_Swings` | One-Arm Kettlebell Swings | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes |
| `One-Arm_Open_Palm_Kettlebell_Clean` | One-Arm Open Palm Kettlebell Clean | hamstrings | músculo: hamstrings; músculo: glutes; músculo: quadriceps; patrón: clean |
| `One-Arm_Overhead_Kettlebell_Squats` | One-Arm Overhead Kettlebell Squats | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `One-Arm_Side_Deadlift` | One-Arm Side Deadlift | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: deadlift |
| `One-Legged_Cable_Kickback` | One-Legged Cable Kickback | glutes | músculo: glutes; músculo: hamstrings |
| `One_Half_Locust` | One Half Locust | quadriceps | músculo: quadriceps |
| `One_Knee_To_Chest` | One Knee To Chest | glutes | músculo: glutes; músculo: hamstrings; patrón: knee |
| `One_Leg_Barbell_Squat` | One Leg Barbell Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Open_Palm_Kettlebell_Clean` | Open Palm Kettlebell Clean | hamstrings | músculo: hamstrings; músculo: glutes; músculo: quadriceps; patrón: clean |
| `Overhead_Squat` | Overhead Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Peroneals-SMR` | Peroneals-SMR | calves | músculo: calves |
| `Peroneals_Stretch` | Peroneals Stretch | calves | músculo: calves |
| `Physioball_Hip_Bridge` | Physioball Hip Bridge | glutes | músculo: glutes; músculo: hamstrings |
| `Piriformis-SMR` | Piriformis-SMR | glutes | músculo: glutes |
| `Platform_Hamstring_Slides` | Platform Hamstring Slides | hamstrings | músculo: hamstrings; músculo: glutes; patrón: hamstring |
| `Plie_Dumbbell_Squat` | Plie Dumbbell Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Plyo_Kettlebell_Pushups` | Plyo Kettlebell Pushups | chest | patrón: yoke |
| `Posterior_Tibialis_Stretch` | Posterior Tibialis Stretch | calves | músculo: calves |
| `Power_Clean` | Power Clean | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: clean |
| `Power_Clean_from_Blocks` | Power Clean from Blocks | hamstrings | músculo: hamstrings; músculo: quadriceps; patrón: clean |
| `Power_Jerk` | Power Jerk | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: jerk |
| `Power_Snatch` | Power Snatch | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: snatch |
| `Power_Snatch_from_Blocks` | Power Snatch from Blocks | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: snatch |
| `Power_Stairs` | Power Stairs | hamstrings | músculo: hamstrings; músculo: adductors; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: stair |
| `Prone_Manual_Hamstring` | Prone Manual Hamstring | hamstrings | músculo: hamstrings; patrón: hamstring |
| `Prowler_Sprint` | Prowler Sprint | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: sprint |
| `Pull_Through` | Pull Through | glutes | músculo: glutes; músculo: hamstrings |
| `Push_Press` | Push Press | shoulders | músculo: quadriceps |
| `Push_Press_-_Behind_the_Neck` | Push Press - Behind the Neck | shoulders | músculo: calves; músculo: quadriceps |
| `Quad_Stretch` | Quad Stretch | quadriceps | músculo: quadriceps; patrón: quad |
| `Quadriceps-SMR` | Quadriceps-SMR | quadriceps | músculo: quadriceps; patrón: quad |
| `Quick_Leap` | Quick Leap | quadriceps | músculo: quadriceps; músculo: calves; músculo: hamstrings; patrón: leap |
| `Rack_Pull_with_Bands` | Rack Pull with Bands | lower back | músculo: glutes; músculo: hamstrings; músculo: quadriceps |
| `Rack_Pulls` | Rack Pulls | lower back | músculo: glutes; músculo: hamstrings |
| `Rear_Leg_Raises` | Rear Leg Raises | quadriceps | músculo: quadriceps |
| `Recumbent_Bike` | Recumbent Bike | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: bike |
| `Return_Push_from_Stance` | Return Push from Stance | shoulders | patrón: stance |
| `Reverse_Band_Box_Squat` | Reverse Band Box Squat | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: box |
| `Reverse_Band_Deadlift` | Reverse Band Deadlift | lower back | músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: deadlift |
| `Reverse_Band_Power_Squat` | Reverse Band Power Squat | quadriceps | músculo: quadriceps; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Reverse_Band_Sumo_Deadlift` | Reverse Band Sumo Deadlift | hamstrings | músculo: hamstrings; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: deadlift |
| `Reverse_Hyperextension` | Reverse Hyperextension | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes |
| `Rickshaw_Carry` | Rickshaw Carry | forearms | músculo: calves; músculo: glutes; músculo: hamstrings; músculo: quadriceps |
| `Rickshaw_Deadlift` | Rickshaw Deadlift | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: deadlift |
| `Rocket_Jump` | Rocket Jump | quadriceps | músculo: quadriceps; músculo: calves; músculo: hamstrings; patrón: jump; patrón: rocket |
| `Rocking_Standing_Calf_Raise` | Rocking Standing Calf Raise | calves | músculo: calves |
| `Romanian_Deadlift` | Romanian Deadlift | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; patrón: deadlift |
| `Romanian_Deadlift_from_Deficit` | Romanian Deadlift from Deficit | hamstrings | músculo: hamstrings; músculo: glutes; patrón: deadlift |
| `Rope_Jumping` | Rope Jumping | quadriceps | músculo: quadriceps; músculo: calves; músculo: hamstrings; patrón: jump |
| `Rowing_Stationary` | Rowing, Stationary | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: rowing |
| `Runners_Stretch` | Runner's Stretch | hamstrings | músculo: hamstrings; músculo: calves |
| `Running_Treadmill` | Running, Treadmill | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: running; patrón: treadmill |
| `Sandbag_Load` | Sandbag Load | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings |
| `Scissors_Jump` | Scissors Jump | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: jump |
| `Seated_Band_Hamstring_Curl` | Seated Band Hamstring Curl | hamstrings | músculo: hamstrings; patrón: hamstring |
| `Seated_Calf_Raise` | Seated Calf Raise | calves | músculo: calves |
| `Seated_Calf_Stretch` | Seated Calf Stretch | calves | músculo: calves; músculo: hamstrings |
| `Seated_Floor_Hamstring_Stretch` | Seated Floor Hamstring Stretch | hamstrings | músculo: hamstrings; músculo: calves; patrón: hamstring |
| `Seated_Glute` | Seated Glute | glutes | músculo: glutes; músculo: adductors |
| `Seated_Good_Mornings` | Seated Good Mornings | lower back | músculo: glutes |
| `Seated_Hamstring` | Seated Hamstring | hamstrings | músculo: hamstrings; músculo: calves; patrón: hamstring |
| `Seated_Hamstring_and_Calf_Stretch` | Seated Hamstring and Calf Stretch | hamstrings | músculo: hamstrings; músculo: calves; patrón: hamstring |
| `Seated_Head_Harness_Neck_Resistance` | Seated Head Harness Neck Resistance | neck | patrón: stance |
| `Seated_Leg_Curl` | Seated Leg Curl | hamstrings | músculo: hamstrings; patrón: leg curl |
| `Seated_Leg_Tucks` | Seated Leg Tucks | abdominals | patrón: tuck |
| `Side_Hop-Sprint` | Side Hop-Sprint | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: hamstrings; patrón: hops; patrón: sprint |
| `Side_Leg_Raises` | Side Leg Raises | adductors | músculo: adductors |
| `Side_Lying_Groin_Stretch` | Side Lying Groin Stretch | adductors | músculo: adductors; músculo: hamstrings |
| `Side_Standing_Long_Jump` | Side Standing Long Jump | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: jump |
| `Side_to_Side_Box_Shuffle` | Side to Side Box Shuffle | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: hamstrings; patrón: box; patrón: shuffle |
| `Single-Cone_Sprint_Drill` | Single-Cone Sprint Drill | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: sprint; patrón: cone |
| `Single-Leg_High_Box_Squat` | Single-Leg High Box Squat | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: box |
| `Single-Leg_Hop_Progression` | Single-Leg Hop Progression | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: hamstrings |
| `Single-Leg_Lateral_Hop` | Single-Leg Lateral Hop | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: hamstrings |
| `Single-Leg_Leg_Extension` | Single-Leg Leg Extension | quadriceps | músculo: quadriceps; patrón: leg extension |
| `Single-Leg_Stride_Jump` | Single-Leg Stride Jump | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: hamstrings; patrón: jump |
| `Single_Leg_Butt_Kick` | Single Leg Butt Kick | quadriceps | músculo: quadriceps; músculo: calves; músculo: hamstrings |
| `Single_Leg_Glute_Bridge` | Single Leg Glute Bridge | glutes | músculo: glutes; músculo: hamstrings |
| `Single_Leg_Push-off` | Single Leg Push-off | quadriceps | músculo: quadriceps; músculo: calves; músculo: hamstrings |
| `Sit_Squats` | Sit Squats | quadriceps | músculo: quadriceps; músculo: abductors; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Skating` | Skating | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: skating |
| `Sled_Drag_-_Harness` | Sled Drag - Harness | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: sled |
| `Sled_Overhead_Backward_Walk` | Sled Overhead Backward Walk | shoulders | músculo: calves; músculo: quadriceps; patrón: walk; patrón: sled |
| `Sled_Overhead_Triceps_Extension` | Sled Overhead Triceps Extension | triceps | patrón: sled |
| `Sled_Push` | Sled Push | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: sled |
| `Sled_Reverse_Flye` | Sled Reverse Flye | shoulders | patrón: sled |
| `Sled_Row` | Sled Row | middle back | patrón: sled |
| `Sledgehammer_Swings` | Sledgehammer Swings | abdominals | músculo: calves; patrón: sled |
| `Smith_Machine_Calf_Raise` | Smith Machine Calf Raise | calves | músculo: calves |
| `Smith_Machine_Hang_Power_Clean` | Smith Machine Hang Power Clean | hamstrings | músculo: hamstrings; músculo: glutes; músculo: quadriceps; patrón: clean |
| `Smith_Machine_Leg_Press` | Smith Machine Leg Press | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: leg press |
| `Smith_Machine_Pistol_Squat` | Smith Machine Pistol Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: pistol |
| `Smith_Machine_Reverse_Calf_Raises` | Smith Machine Reverse Calf Raises | calves | músculo: calves |
| `Smith_Machine_Squat` | Smith Machine Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Smith_Machine_Stiff-Legged_Deadlift` | Smith Machine Stiff-Legged Deadlift | hamstrings | músculo: hamstrings; músculo: glutes; patrón: deadlift |
| `Smith_Single-Leg_Split_Squat` | Smith Single-Leg Split Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: split |
| `Snatch` | Snatch | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: snatch |
| `Snatch_Balance` | Snatch Balance | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: snatch |
| `Snatch_Deadlift` | Snatch Deadlift | hamstrings | músculo: hamstrings; músculo: glutes; músculo: quadriceps; patrón: snatch; patrón: deadlift |
| `Snatch_Pull` | Snatch Pull | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: snatch |
| `Snatch_Shrug` | Snatch Shrug | traps | patrón: snatch |
| `Snatch_from_Blocks` | Snatch from Blocks | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: snatch |
| `Speed_Box_Squat` | Speed Box Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: box |
| `Speed_Squats` | Speed Squats | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Spell_Caster` | Spell Caster | abdominals | músculo: glutes |
| `Spider_Crawl` | Spider Crawl | abdominals | patrón: crawl |
| `Split_Clean` | Split Clean | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: split; patrón: clean |
| `Split_Jerk` | Split Jerk | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: split; patrón: jerk |
| `Split_Jump` | Split Jump | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: jump; patrón: split |
| `Split_Snatch` | Split Snatch | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: split; patrón: snatch |
| `Split_Squat_with_Dumbbells` | Split Squat with Dumbbells | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: split |
| `Split_Squats` | Split Squats | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps; patrón: squat; patrón: split |
| `Squat_Jerk` | Squat Jerk | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: jerk |
| `Squat_with_Bands` | Squat with Bands | quadriceps | músculo: quadriceps; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Squat_with_Chains` | Squat with Chains | quadriceps | músculo: quadriceps; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Squat_with_Plate_Movers` | Squat with Plate Movers | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Squats_-_With_Bands` | Squats - With Bands | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Stairmaster` | Stairmaster | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: stair |
| `Standing_Barbell_Calf_Raise` | Standing Barbell Calf Raise | calves | músculo: calves |
| `Standing_Cable_Wood_Chop` | Standing Cable Wood Chop | abdominals | patrón: wood chop; patrón: woodchop |
| `Standing_Calf_Raises` | Standing Calf Raises | calves | músculo: calves |
| `Standing_Dumbbell_Calf_Raise` | Standing Dumbbell Calf Raise | calves | músculo: calves |
| `Standing_Elevated_Quad_Stretch` | Standing Elevated Quad Stretch | quadriceps | músculo: quadriceps; patrón: quad |
| `Standing_Gastrocnemius_Calf_Stretch` | Standing Gastrocnemius Calf Stretch | calves | músculo: calves; músculo: hamstrings |
| `Standing_Hamstring_and_Calf_Stretch` | Standing Hamstring and Calf Stretch | hamstrings | músculo: hamstrings; patrón: hamstring |
| `Standing_Hip_Circles` | Standing Hip Circles | abductors | músculo: abductors; músculo: adductors |
| `Standing_Hip_Flexors` | Standing Hip Flexors | quadriceps | músculo: quadriceps |
| `Standing_Leg_Curl` | Standing Leg Curl | hamstrings | músculo: hamstrings; patrón: leg curl |
| `Standing_Long_Jump` | Standing Long Jump | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: jump |
| `Standing_Pelvic_Tilt` | Standing Pelvic Tilt | lower back | músculo: glutes |
| `Standing_Soleus_And_Achilles_Stretch` | Standing Soleus And Achilles Stretch | calves | músculo: calves |
| `Standing_Toe_Touches` | Standing Toe Touches | hamstrings | músculo: hamstrings; músculo: calves |
| `Standing_Two-Arm_Overhead_Throw` | Standing Two-Arm Overhead Throw | shoulders | patrón: throw |
| `Star_Jump` | Star Jump | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: jump |
| `Step-up_with_Knee_Raise` | Step-up with Knee Raise | glutes | músculo: glutes; músculo: hamstrings; músculo: quadriceps; patrón: step up; patrón: stepup; patrón: knee |
| `Step_Mill` | Step Mill | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: step mill |
| `Stiff-Legged_Barbell_Deadlift` | Stiff-Legged Barbell Deadlift | hamstrings | músculo: hamstrings; músculo: glutes; patrón: deadlift |
| `Stiff-Legged_Dumbbell_Deadlift` | Stiff-Legged Dumbbell Deadlift | hamstrings | músculo: hamstrings; músculo: glutes; patrón: deadlift |
| `Stiff_Leg_Barbell_Good_Morning` | Stiff Leg Barbell Good Morning | lower back | músculo: glutes; músculo: hamstrings |
| `Stride_Jump_Crossover` | Stride Jump Crossover | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: hamstrings; patrón: jump |
| `Sumo_Deadlift` | Sumo Deadlift | hamstrings | músculo: hamstrings; músculo: adductors; músculo: glutes; músculo: quadriceps; patrón: deadlift |
| `Sumo_Deadlift_with_Bands` | Sumo Deadlift with Bands | hamstrings | músculo: hamstrings; músculo: adductors; músculo: glutes; músculo: quadriceps; patrón: deadlift |
| `Sumo_Deadlift_with_Chains` | Sumo Deadlift with Chains | hamstrings | músculo: hamstrings; músculo: abductors; músculo: adductors; músculo: glutes; músculo: quadriceps; patrón: deadlift |
| `Superman` | Superman | lower back | músculo: glutes; músculo: hamstrings |
| `Supine_Chest_Throw` | Supine Chest Throw | triceps | patrón: throw |
| `Supine_One-Arm_Overhead_Throw` | Supine One-Arm Overhead Throw | abdominals | patrón: throw |
| `Supine_Two-Arm_Overhead_Throw` | Supine Two-Arm Overhead Throw | abdominals | patrón: throw |
| `Suspended_Fallout` | Suspended Fallout | abdominals | patrón: fallout |
| `Suspended_Split_Squat` | Suspended Split Squat | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: split |
| `The_Straddle` | The Straddle | hamstrings | músculo: hamstrings; músculo: adductors; músculo: calves |
| `Thigh_Abductor` | Thigh Abductor | abductors | músculo: abductors; músculo: glutes |
| `Thigh_Adductor` | Thigh Adductor | adductors | músculo: adductors; músculo: glutes; músculo: hamstrings |
| `Tire_Flip` | Tire Flip | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: tire flip |
| `Trail_Running_Walking` | Trail Running/Walking | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: running; patrón: walk |
| `Trap_Bar_Deadlift` | Trap Bar Deadlift | quadriceps | músculo: quadriceps; músculo: glutes; músculo: hamstrings; patrón: deadlift |
| `Tuck_Crunch` | Tuck Crunch | abdominals | patrón: tuck |
| `Two-Arm_Kettlebell_Clean` | Two-Arm Kettlebell Clean | shoulders | músculo: calves; músculo: glutes; músculo: hamstrings; patrón: clean |
| `Two-Arm_Kettlebell_Jerk` | Two-Arm Kettlebell Jerk | shoulders | músculo: calves; músculo: quadriceps; patrón: jerk |
| `Upper_Back-Leg_Grab` | Upper Back-Leg Grab | hamstrings | músculo: hamstrings |
| `Vertical_Swing` | Vertical Swing | hamstrings | músculo: hamstrings; músculo: glutes; músculo: quadriceps |
| `Walking_Treadmill` | Walking, Treadmill | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: walk; patrón: treadmill |
| `Weighted_Ball_Hyperextension` | Weighted Ball Hyperextension | lower back | músculo: glutes; músculo: hamstrings |
| `Weighted_Jump_Squat` | Weighted Jump Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: jump |
| `Weighted_Sissy_Squat` | Weighted Sissy Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: sissy |
| `Weighted_Squat` | Weighted Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Wide_Stance_Barbell_Squat` | Wide Stance Barbell Squat | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat; patrón: stance |
| `Wide_Stance_Stiff_Legs` | Wide Stance Stiff Legs | hamstrings | músculo: hamstrings; músculo: adductors; músculo: glutes; patrón: stance |
| `Wind_Sprints` | Wind Sprints | abdominals | patrón: sprint |
| `Windmills` | Windmills | abductors | músculo: abductors; músculo: glutes; músculo: hamstrings |
| `Worlds_Greatest_Stretch` | World's Greatest Stretch | hamstrings | músculo: hamstrings; músculo: calves; músculo: glutes; músculo: quadriceps |
| `Yoke_Walk` | Yoke Walk | quadriceps | músculo: quadriceps; músculo: abductors; músculo: adductors; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: walk; patrón: yoke |
| `Zercher_Squats` | Zercher Squats | quadriceps | músculo: quadriceps; músculo: calves; músculo: glutes; músculo: hamstrings; patrón: squat |

## `zona_lumbar` (649 bloqueados)

- Músculos: abdominals, glutes, hamstrings, lower back
- Patrones: `deadlift`, `good morning`, `hyperextension`, `back extension`, `bent over`, `clean`, `snatch`, `jerk`, `squat`, `lunge`, `thruster`, `leg press`, `romanian`, `stiff leg`, `pull through`, `rack pull`, `high pull`, `swing`, `pass between`, `figure 8`, `superman`, `locust`, `row`, `shrug`, `overhead`, `military`, `push press`, `handstand`, `standing`, `powerlifting`, `sit up`, `situp`, `crunch`, `v up`, `jackknife`, `leg raise`, `rollout`, `ab roller`, `fallout`, `twist`, `rotation`, `wood chop`, `woodchop`, `windmill`, `side bend`, `landmine`, `muscle up`, `kipping`, `rope`, `atlas stone`, `stone`, `log lift`, `tire flip`, `yoke`, `farmer`, `rickshaw`, `keg`, `sandbag`, `sled`, `drag`, `car driver`, `throw`, `slam`, `chest push`, `stance`, `heavy bag`, `rack delivery`, `bridge`, `hip thrust`, `pullover`, `hanging`, `jump`, `hops`, `bound`, `leap`, `skip`, `sprint`, `running`, `jog`, `skating`, `mountain climber`, `burpee`, `box`, `step up`, `stepup`, `bicycl`, `bike`, `shoulder press`, `kettlebell`, `seesaw`, `see saw`, `para press`, `arnold`, `bradford`, `cuban press`, `seated dumbbell press`, `dumbbell one arm triceps extension`, `seated triceps press`, `anti gravity`, `jammer`, `medicine ball`, `power partials`, `calf raise`, `donkey`, `monster walk`, `groiner`, `bench press`, `board press`, `pin press`, `push up`, `pushup`, `plyo`, `drop push`, `hip flexor`, `iron crosses`, `lying crossover`, `looking at ceiling`, `back`
- Ids extra: (ninguno)

| Id | Nombre | Músculo primario | Motivo |
|---|---|---|---|
| `3_4_Sit-Up` | 3/4 Sit-Up | abdominals | músculo: abdominals; patrón: sit up; patrón: situp |
| `90_90_Hamstring` | 90/90 Hamstring | hamstrings | músculo: hamstrings |
| `Ab_Crunch_Machine` | Ab Crunch Machine | abdominals | músculo: abdominals; patrón: crunch |
| `Ab_Roller` | Ab Roller | abdominals | músculo: abdominals; patrón: ab roller |
| `Advanced_Kettlebell_Windmill` | Advanced Kettlebell Windmill | abdominals | músculo: abdominals; músculo: glutes; músculo: hamstrings; patrón: windmill; patrón: kettlebell |
| `Air_Bike` | Air Bike | abdominals | músculo: abdominals; patrón: bike |
| `Alternate_Heel_Touchers` | Alternate Heel Touchers | abdominals | músculo: abdominals |
| `Alternate_Leg_Diagonal_Bound` | Alternate Leg Diagonal Bound | quadriceps | músculo: glutes; músculo: hamstrings; patrón: bound |
| `Alternating_Cable_Shoulder_Press` | Alternating Cable Shoulder Press | shoulders | patrón: shoulder press |
| `Alternating_Floor_Press` | Alternating Floor Press | chest | músculo: abdominals |
| `Alternating_Hang_Clean` | Alternating Hang Clean | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: clean |
| `Alternating_Kettlebell_Press` | Alternating Kettlebell Press | shoulders | patrón: kettlebell |
| `Alternating_Kettlebell_Row` | Alternating Kettlebell Row | middle back | patrón: row; patrón: kettlebell |
| `Alternating_Renegade_Row` | Alternating Renegade Row | middle back | músculo: abdominals; patrón: row |
| `Ankle_On_The_Knee` | Ankle On The Knee | glutes | músculo: glutes |
| `Anti-Gravity_Press` | Anti-Gravity Press | shoulders | patrón: anti gravity |
| `Arnold_Dumbbell_Press` | Arnold Dumbbell Press | shoulders | patrón: arnold |
| `Atlas_Stone_Trainer` | Atlas Stone Trainer | lower back | músculo: lower back; músculo: glutes; músculo: hamstrings; patrón: atlas stone; patrón: stone |
| `Atlas_Stones` | Atlas Stones | lower back | músculo: lower back; músculo: abdominals; músculo: glutes; músculo: hamstrings; patrón: atlas stone; patrón: stone |
| `Axle_Deadlift` | Axle Deadlift | lower back | músculo: lower back; músculo: glutes; músculo: hamstrings; patrón: deadlift |
| `Back_Flyes_-_With_Bands` | Back Flyes - With Bands | shoulders | patrón: back |
| `Backward_Drag` | Backward Drag | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: drag; patrón: back |
| `Backward_Medicine_Ball_Throw` | Backward Medicine Ball Throw | shoulders | patrón: row; patrón: throw; patrón: medicine ball; patrón: back |
| `Balance_Board` | Balance Board | calves | músculo: hamstrings |
| `Ball_Leg_Curl` | Ball Leg Curl | hamstrings | músculo: hamstrings; músculo: glutes |
| `Band_Assisted_Pull-Up` | Band Assisted Pull-Up | lats | músculo: abdominals |
| `Band_Good_Morning` | Band Good Morning | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: good morning |
| `Band_Good_Morning_Pull_Through` | Band Good Morning (Pull Through) | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: good morning; patrón: pull through |
| `Barbell_Ab_Rollout` | Barbell Ab Rollout | abdominals | músculo: abdominals; músculo: lower back; patrón: rollout |
| `Barbell_Ab_Rollout_-_On_Knees` | Barbell Ab Rollout - On Knees | abdominals | músculo: abdominals; músculo: lower back; patrón: rollout |
| `Barbell_Bench_Press_-_Medium_Grip` | Barbell Bench Press - Medium Grip | chest | patrón: bench press |
| `Barbell_Deadlift` | Barbell Deadlift | lower back | músculo: lower back; músculo: glutes; músculo: hamstrings; patrón: deadlift |
| `Barbell_Full_Squat` | Barbell Full Squat | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: squat |
| `Barbell_Glute_Bridge` | Barbell Glute Bridge | glutes | músculo: glutes; músculo: hamstrings; patrón: bridge |
| `Barbell_Guillotine_Bench_Press` | Barbell Guillotine Bench Press | chest | patrón: bench press |
| `Barbell_Hack_Squat` | Barbell Hack Squat | quadriceps | músculo: hamstrings; patrón: squat |
| `Barbell_Hip_Thrust` | Barbell Hip Thrust | glutes | músculo: glutes; músculo: hamstrings; patrón: hip thrust |
| `Barbell_Incline_Bench_Press_-_Medium_Grip` | Barbell Incline Bench Press - Medium Grip | chest | patrón: bench press |
| `Barbell_Lunge` | Barbell Lunge | quadriceps | músculo: glutes; músculo: hamstrings; patrón: lunge |
| `Barbell_Rear_Delt_Row` | Barbell Rear Delt Row | shoulders | patrón: row |
| `Barbell_Rollout_from_Bench` | Barbell Rollout from Bench | abdominals | músculo: abdominals; músculo: glutes; músculo: hamstrings; patrón: rollout |
| `Barbell_Seated_Calf_Raise` | Barbell Seated Calf Raise | calves | patrón: calf raise |
| `Barbell_Shoulder_Press` | Barbell Shoulder Press | shoulders | patrón: shoulder press |
| `Barbell_Shrug` | Barbell Shrug | traps | patrón: shrug |
| `Barbell_Shrug_Behind_The_Back` | Barbell Shrug Behind The Back | traps | patrón: shrug; patrón: back |
| `Barbell_Side_Bend` | Barbell Side Bend | abdominals | músculo: abdominals; músculo: lower back; patrón: side bend |
| `Barbell_Side_Split_Squat` | Barbell Side Split Squat | quadriceps | músculo: hamstrings; músculo: lower back; patrón: squat |
| `Barbell_Squat` | Barbell Squat | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: squat |
| `Barbell_Squat_To_A_Bench` | Barbell Squat To A Bench | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: squat |
| `Barbell_Step_Ups` | Barbell Step Ups | quadriceps | músculo: glutes; músculo: hamstrings; patrón: step up; patrón: stepup |
| `Barbell_Walking_Lunge` | Barbell Walking Lunge | quadriceps | músculo: glutes; músculo: hamstrings; patrón: lunge |
| `Battling_Ropes` | Battling Ropes | shoulders | patrón: rope |
| `Bear_Crawl_Sled_Drags` | Bear Crawl Sled Drags | quadriceps | músculo: glutes; músculo: hamstrings; patrón: sled; patrón: drag |
| `Bench_Jump` | Bench Jump | quadriceps | músculo: glutes; músculo: hamstrings; patrón: jump |
| `Bench_Press_-_Powerlifting` | Bench Press - Powerlifting | triceps | patrón: powerlifting; patrón: bench press |
| `Bench_Press_-_With_Bands` | Bench Press - With Bands | chest | patrón: bench press |
| `Bench_Press_with_Chains` | Bench Press with Chains | triceps | patrón: bench press |
| `Bench_Sprint` | Bench Sprint | quadriceps | músculo: glutes; músculo: hamstrings; patrón: sprint |
| `Bent-Arm_Barbell_Pullover` | Bent-Arm Barbell Pullover | lats | patrón: pullover |
| `Bent-Arm_Dumbbell_Pullover` | Bent-Arm Dumbbell Pullover | chest | patrón: pullover |
| `Bent-Knee_Hip_Raise` | Bent-Knee Hip Raise | abdominals | músculo: abdominals |
| `Bent_Over_Barbell_Row` | Bent Over Barbell Row | middle back | patrón: bent over; patrón: row |
| `Bent_Over_Dumbbell_Rear_Delt_Raise_With_Head_On_Bench` | Bent Over Dumbbell Rear Delt Raise With Head On Bench | shoulders | patrón: bent over |
| `Bent_Over_Low-Pulley_Side_Lateral` | Bent Over Low-Pulley Side Lateral | shoulders | músculo: lower back; patrón: bent over |
| `Bent_Over_One-Arm_Long_Bar_Row` | Bent Over One-Arm Long Bar Row | middle back | músculo: lower back; patrón: bent over; patrón: row |
| `Bent_Over_Two-Arm_Long_Bar_Row` | Bent Over Two-Arm Long Bar Row | middle back | patrón: bent over; patrón: row |
| `Bent_Over_Two-Dumbbell_Row` | Bent Over Two-Dumbbell Row | middle back | patrón: bent over; patrón: row |
| `Bent_Over_Two-Dumbbell_Row_With_Palms_In` | Bent Over Two-Dumbbell Row With Palms In | middle back | patrón: bent over; patrón: row |
| `Bent_Press` | Bent Press | abdominals | músculo: abdominals; músculo: glutes; músculo: hamstrings; músculo: lower back |
| `Bicycling` | Bicycling | quadriceps | músculo: glutes; músculo: hamstrings; patrón: bicycl |
| `Bicycling_Stationary` | Bicycling, Stationary | quadriceps | músculo: glutes; músculo: hamstrings; patrón: bicycl |
| `Board_Press` | Board Press | triceps | patrón: board press |
| `Body-Up` | Body-Up | triceps | músculo: abdominals |
| `Bodyweight_Flyes` | Bodyweight Flyes | chest | músculo: abdominals |
| `Bodyweight_Mid_Row` | Bodyweight Mid Row | middle back | patrón: row |
| `Bodyweight_Squat` | Bodyweight Squat | quadriceps | músculo: glutes; músculo: hamstrings; patrón: squat |
| `Bodyweight_Walking_Lunge` | Bodyweight Walking Lunge | quadriceps | músculo: glutes; músculo: hamstrings; patrón: lunge |
| `Bosu_Ball_Cable_Crunch_With_Side_Bends` | Bosu Ball Cable Crunch With Side Bends | abdominals | músculo: abdominals; patrón: crunch; patrón: side bend |
| `Bottoms-Up_Clean_From_The_Hang_Position` | Bottoms-Up Clean From The Hang Position | forearms | patrón: clean |
| `Bottoms_Up` | Bottoms Up | abdominals | músculo: abdominals |
| `Box_Jump_Multiple_Response` | Box Jump (Multiple Response) | hamstrings | músculo: hamstrings; músculo: glutes; patrón: jump; patrón: box |
| `Box_Skip` | Box Skip | hamstrings | músculo: hamstrings; músculo: glutes; patrón: skip; patrón: box |
| `Box_Squat` | Box Squat | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: squat; patrón: box |
| `Box_Squat_with_Bands` | Box Squat with Bands | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: squat; patrón: box |
| `Box_Squat_with_Chains` | Box Squat with Chains | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: squat; patrón: box |
| `Bradford_Rocky_Presses` | Bradford/Rocky Presses | shoulders | patrón: bradford |
| `Butt-Ups` | Butt-Ups | abdominals | músculo: abdominals |
| `Butt_Lift_Bridge` | Butt Lift (Bridge) | glutes | músculo: glutes; músculo: hamstrings; patrón: bridge |
| `Cable_Crunch` | Cable Crunch | abdominals | músculo: abdominals; patrón: crunch |
| `Cable_Deadlifts` | Cable Deadlifts | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: deadlift |
| `Cable_Hammer_Curls_-_Rope_Attachment` | Cable Hammer Curls - Rope Attachment | biceps | patrón: rope |
| `Cable_Internal_Rotation` | Cable Internal Rotation | shoulders | patrón: rotation |
| `Cable_Judo_Flip` | Cable Judo Flip | abdominals | músculo: abdominals |
| `Cable_Reverse_Crunch` | Cable Reverse Crunch | abdominals | músculo: abdominals; patrón: crunch |
| `Cable_Rope_Overhead_Triceps_Extension` | Cable Rope Overhead Triceps Extension | triceps | patrón: overhead; patrón: rope |
| `Cable_Rope_Rear-Delt_Rows` | Cable Rope Rear-Delt Rows | shoulders | patrón: row; patrón: rope |
| `Cable_Russian_Twists` | Cable Russian Twists | abdominals | músculo: abdominals; patrón: twist |
| `Cable_Seated_Crunch` | Cable Seated Crunch | abdominals | músculo: abdominals; patrón: crunch |
| `Cable_Shoulder_Press` | Cable Shoulder Press | shoulders | patrón: shoulder press |
| `Cable_Shrugs` | Cable Shrugs | traps | patrón: shrug |
| `Calf-Machine_Shoulder_Shrug` | Calf-Machine Shoulder Shrug | traps | patrón: shrug |
| `Calf_Press_On_The_Leg_Press_Machine` | Calf Press On The Leg Press Machine | calves | patrón: leg press |
| `Calf_Raise_On_A_Dumbbell` | Calf Raise On A Dumbbell | calves | patrón: calf raise |
| `Calf_Raises_-_With_Bands` | Calf Raises - With Bands | calves | patrón: calf raise |
| `Car_Deadlift` | Car Deadlift | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: deadlift |
| `Car_Drivers` | Car Drivers | shoulders | patrón: car driver |
| `Carioca_Quick_Step` | Carioca Quick Step | adductors | músculo: abdominals; músculo: glutes; músculo: hamstrings |
| `Cat_Stretch` | Cat Stretch | lower back | músculo: lower back |
| `Catch_and_Overhead_Throw` | Catch and Overhead Throw | lats | músculo: abdominals; patrón: row; patrón: overhead; patrón: throw |
| `Chair_Leg_Extended_Stretch` | Chair Leg Extended Stretch | hamstrings | músculo: hamstrings |
| `Chair_Lower_Back_Stretch` | Chair Lower Back Stretch | lats | músculo: lower back; patrón: back |
| `Chair_Squat` | Chair Squat | quadriceps | músculo: glutes; músculo: hamstrings; patrón: squat |
| `Chest_Push_from_3_point_stance` | Chest Push from 3 point stance | chest | músculo: abdominals; patrón: chest push; patrón: stance |
| `Chest_Push_multiple_response` | Chest Push (multiple response) | chest | músculo: abdominals; patrón: chest push |
| `Chest_Push_single_response` | Chest Push (single response) | chest | músculo: abdominals; patrón: chest push |
| `Chest_Push_with_Run_Release` | Chest Push with Run Release | chest | músculo: abdominals; patrón: chest push |
| `Childs_Pose` | Child's Pose | lower back | músculo: lower back; músculo: glutes |
| `Circus_Bell` | Circus Bell | shoulders | músculo: glutes; músculo: hamstrings; músculo: lower back |
| `Clean` | Clean | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: clean |
| `Clean_Deadlift` | Clean Deadlift | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: deadlift; patrón: clean |
| `Clean_Pull` | Clean Pull | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: clean |
| `Clean_Shrug` | Clean Shrug | traps | patrón: clean; patrón: shrug |
| `Clean_and_Jerk` | Clean and Jerk | shoulders | músculo: abdominals; músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: clean; patrón: jerk |
| `Clean_and_Press` | Clean and Press | shoulders | músculo: abdominals; músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: clean |
| `Clean_from_Blocks` | Clean from Blocks | quadriceps | músculo: glutes; músculo: hamstrings; patrón: clean |
| `Clock_Push-Up` | Clock Push-Up | chest | patrón: push up; patrón: pushup |
| `Close-Grip_Barbell_Bench_Press` | Close-Grip Barbell Bench Press | triceps | patrón: bench press |
| `Close-Grip_Push-Up_off_of_a_Dumbbell` | Close-Grip Push-Up off of a Dumbbell | triceps | músculo: abdominals; patrón: push up; patrón: pushup |
| `Close-Grip_Standing_Barbell_Curl` | Close-Grip Standing Barbell Curl | biceps | patrón: standing |
| `Cocoons` | Cocoons | abdominals | músculo: abdominals |
| `Conans_Wheel` | Conan's Wheel | quadriceps | músculo: abdominals; músculo: lower back |
| `Cross-Body_Crunch` | Cross-Body Crunch | abdominals | músculo: abdominals; patrón: crunch |
| `Crossover_Reverse_Lunge` | Crossover Reverse Lunge | lower back | músculo: lower back; músculo: abdominals; músculo: glutes; músculo: hamstrings; patrón: lunge |
| `Crunch_-_Hands_Overhead` | Crunch - Hands Overhead | abdominals | músculo: abdominals; patrón: overhead; patrón: crunch |
| `Crunch_-_Legs_On_Exercise_Ball` | Crunch - Legs On Exercise Ball | abdominals | músculo: abdominals; patrón: crunch |
| `Crunches` | Crunches | abdominals | músculo: abdominals; patrón: crunch |
| `Cuban_Press` | Cuban Press | shoulders | patrón: cuban press |
| `Dancers_Stretch` | Dancer's Stretch | lower back | músculo: lower back; músculo: glutes |
| `Dead_Bug` | Dead Bug | abdominals | músculo: abdominals |
| `Deadlift_with_Bands` | Deadlift with Bands | lower back | músculo: lower back; músculo: glutes; músculo: hamstrings; patrón: deadlift |
| `Deadlift_with_Chains` | Deadlift with Chains | lower back | músculo: lower back; músculo: glutes; músculo: hamstrings; patrón: deadlift |
| `Decline_Barbell_Bench_Press` | Decline Barbell Bench Press | chest | patrón: bench press |
| `Decline_Crunch` | Decline Crunch | abdominals | músculo: abdominals; patrón: crunch |
| `Decline_Dumbbell_Bench_Press` | Decline Dumbbell Bench Press | chest | patrón: bench press |
| `Decline_Oblique_Crunch` | Decline Oblique Crunch | abdominals | músculo: abdominals; patrón: crunch |
| `Decline_Push-Up` | Decline Push-Up | chest | patrón: push up; patrón: pushup |
| `Decline_Reverse_Crunch` | Decline Reverse Crunch | abdominals | músculo: abdominals; patrón: crunch |
| `Deficit_Deadlift` | Deficit Deadlift | lower back | músculo: lower back; músculo: glutes; músculo: hamstrings; patrón: deadlift |
| `Depth_Jump_Leap` | Depth Jump Leap | quadriceps | músculo: glutes; músculo: hamstrings; patrón: jump; patrón: leap |
| `Donkey_Calf_Raises` | Donkey Calf Raises | calves | patrón: calf raise; patrón: donkey |
| `Double_Kettlebell_Alternating_Hang_Clean` | Double Kettlebell Alternating Hang Clean | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: clean; patrón: kettlebell |
| `Double_Kettlebell_Jerk` | Double Kettlebell Jerk | shoulders | patrón: jerk; patrón: kettlebell |
| `Double_Kettlebell_Push_Press` | Double Kettlebell Push Press | shoulders | patrón: push press; patrón: kettlebell |
| `Double_Kettlebell_Snatch` | Double Kettlebell Snatch | shoulders | músculo: glutes; músculo: hamstrings; patrón: snatch; patrón: kettlebell |
| `Double_Kettlebell_Windmill` | Double Kettlebell Windmill | abdominals | músculo: abdominals; músculo: glutes; músculo: hamstrings; patrón: windmill; patrón: kettlebell |
| `Double_Leg_Butt_Kick` | Double Leg Butt Kick | quadriceps | músculo: glutes; músculo: hamstrings |
| `Downward_Facing_Balance` | Downward Facing Balance | glutes | músculo: glutes; músculo: abdominals; músculo: hamstrings |
| `Drag_Curl` | Drag Curl | biceps | patrón: drag |
| `Drop_Push` | Drop Push | chest | patrón: drop push |
| `Dumbbell_Bench_Press` | Dumbbell Bench Press | chest | patrón: bench press |
| `Dumbbell_Bench_Press_with_Neutral_Grip` | Dumbbell Bench Press with Neutral Grip | chest | patrón: bench press |
| `Dumbbell_Clean` | Dumbbell Clean | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: clean |
| `Dumbbell_Incline_Row` | Dumbbell Incline Row | middle back | patrón: row |
| `Dumbbell_Lunges` | Dumbbell Lunges | quadriceps | músculo: glutes; músculo: hamstrings; patrón: lunge |
| `Dumbbell_One-Arm_Shoulder_Press` | Dumbbell One-Arm Shoulder Press | shoulders | patrón: shoulder press |
| `Dumbbell_One-Arm_Triceps_Extension` | Dumbbell One-Arm Triceps Extension | triceps | patrón: dumbbell one arm triceps extension |
| `Dumbbell_One-Arm_Upright_Row` | Dumbbell One-Arm Upright Row | shoulders | patrón: row |
| `Dumbbell_Rear_Lunge` | Dumbbell Rear Lunge | quadriceps | músculo: glutes; músculo: hamstrings; patrón: lunge |
| `Dumbbell_Seated_Box_Jump` | Dumbbell Seated Box Jump | quadriceps | músculo: glutes; músculo: hamstrings; patrón: jump; patrón: box |
| `Dumbbell_Seated_One-Leg_Calf_Raise` | Dumbbell Seated One-Leg Calf Raise | calves | patrón: calf raise |
| `Dumbbell_Shoulder_Press` | Dumbbell Shoulder Press | shoulders | patrón: shoulder press |
| `Dumbbell_Shrug` | Dumbbell Shrug | traps | patrón: shrug |
| `Dumbbell_Side_Bend` | Dumbbell Side Bend | abdominals | músculo: abdominals; patrón: side bend |
| `Dumbbell_Squat` | Dumbbell Squat | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: squat |
| `Dumbbell_Squat_To_A_Bench` | Dumbbell Squat To A Bench | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: squat |
| `Dumbbell_Step_Ups` | Dumbbell Step Ups | quadriceps | músculo: glutes; músculo: hamstrings; patrón: step up; patrón: stepup |
| `Dynamic_Back_Stretch` | Dynamic Back Stretch | lats | patrón: back |
| `Elbow_to_Knee` | Elbow to Knee | abdominals | músculo: abdominals |
| `Elbows_Back` | Elbows Back | chest | patrón: back |
| `Elevated_Back_Lunge` | Elevated Back Lunge | quadriceps | músculo: glutes; músculo: hamstrings; patrón: lunge; patrón: back |
| `Elevated_Cable_Rows` | Elevated Cable Rows | lats | patrón: row |
| `Elliptical_Trainer` | Elliptical Trainer | quadriceps | músculo: glutes; músculo: hamstrings |
| `Exercise_Ball_Crunch` | Exercise Ball Crunch | abdominals | músculo: abdominals; patrón: crunch |
| `Exercise_Ball_Pull-In` | Exercise Ball Pull-In | abdominals | músculo: abdominals |
| `Extended_Range_One-Arm_Kettlebell_Floor_Press` | Extended Range One-Arm Kettlebell Floor Press | chest | patrón: kettlebell |
| `External_Rotation` | External Rotation | shoulders | patrón: rotation |
| `External_Rotation_with_Band` | External Rotation with Band | shoulders | patrón: rotation |
| `External_Rotation_with_Cable` | External Rotation with Cable | shoulders | patrón: rotation |
| `Farmers_Walk` | Farmer's Walk | forearms | músculo: abdominals; músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: farmer |
| `Fast_Skipping` | Fast Skipping | quadriceps | músculo: glutes; músculo: hamstrings; patrón: kipping; patrón: skip |
| `Flat_Bench_Leg_Pull-In` | Flat Bench Leg Pull-In | abdominals | músculo: abdominals |
| `Flat_Bench_Lying_Leg_Raise` | Flat Bench Lying Leg Raise | abdominals | músculo: abdominals; patrón: leg raise |
| `Floor_Glute-Ham_Raise` | Floor Glute-Ham Raise | hamstrings | músculo: hamstrings; músculo: glutes |
| `Flutter_Kicks` | Flutter Kicks | glutes | músculo: glutes; músculo: hamstrings |
| `Forward_Drag_with_Press` | Forward Drag with Press | chest | músculo: glutes; músculo: hamstrings; patrón: drag |
| `Frankenstein_Squat` | Frankenstein Squat | quadriceps | músculo: abdominals; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Freehand_Jump_Squat` | Freehand Jump Squat | quadriceps | músculo: glutes; músculo: hamstrings; patrón: squat; patrón: jump |
| `Frog_Hops` | Frog Hops | quadriceps | músculo: glutes; músculo: hamstrings; patrón: hops |
| `Frog_Sit-Ups` | Frog Sit-Ups | abdominals | músculo: abdominals; patrón: sit up; patrón: situp |
| `Front_Barbell_Squat` | Front Barbell Squat | quadriceps | músculo: glutes; músculo: hamstrings; patrón: squat |
| `Front_Barbell_Squat_To_A_Bench` | Front Barbell Squat To A Bench | quadriceps | músculo: glutes; músculo: hamstrings; patrón: squat |
| `Front_Box_Jump` | Front Box Jump | hamstrings | músculo: hamstrings; músculo: glutes; patrón: jump; patrón: box |
| `Front_Cone_Hops_or_hurdle_hops` | Front Cone Hops (or hurdle hops) | quadriceps | músculo: glutes; músculo: hamstrings; patrón: hops |
| `Front_Leg_Raises` | Front Leg Raises | hamstrings | músculo: hamstrings; patrón: leg raise |
| `Front_Raise_And_Pullover` | Front Raise And Pullover | chest | patrón: pullover |
| `Front_Squat_Clean_Grip` | Front Squat (Clean Grip) | quadriceps | músculo: abdominals; músculo: glutes; músculo: hamstrings; patrón: clean; patrón: squat |
| `Front_Squats_With_Two_Kettlebells` | Front Squats With Two Kettlebells | quadriceps | músculo: glutes; patrón: squat; patrón: kettlebell |
| `Glute_Ham_Raise` | Glute Ham Raise | hamstrings | músculo: hamstrings; músculo: glutes |
| `Glute_Kickback` | Glute Kickback | glutes | músculo: glutes; músculo: hamstrings; patrón: back |
| `Goblet_Squat` | Goblet Squat | quadriceps | músculo: glutes; músculo: hamstrings; patrón: squat |
| `Good_Morning` | Good Morning | hamstrings | músculo: hamstrings; músculo: abdominals; músculo: glutes; músculo: lower back; patrón: good morning |
| `Good_Morning_off_Pins` | Good Morning off Pins | hamstrings | músculo: hamstrings; músculo: abdominals; músculo: glutes; músculo: lower back; patrón: good morning |
| `Gorilla_Chin_Crunch` | Gorilla Chin/Crunch | abdominals | músculo: abdominals; patrón: crunch |
| `Groin_and_Back_Stretch` | Groin and Back Stretch | adductors | patrón: back |
| `Groiners` | Groiners | adductors | patrón: groiner |
| `Hack_Squat` | Hack Squat | quadriceps | músculo: glutes; músculo: hamstrings; patrón: squat |
| `Hammer_Grip_Incline_DB_Bench_Press` | Hammer Grip Incline DB Bench Press | chest | patrón: bench press |
| `Hamstring-SMR` | Hamstring-SMR | hamstrings | músculo: hamstrings |
| `Hamstring_Stretch` | Hamstring Stretch | hamstrings | músculo: hamstrings |
| `Handstand_Push-Ups` | Handstand Push-Ups | shoulders | patrón: handstand; patrón: push up; patrón: pushup |
| `Hang_Clean` | Hang Clean | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: clean |
| `Hang_Clean_-_Below_the_Knees` | Hang Clean - Below the Knees | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: clean |
| `Hang_Snatch` | Hang Snatch | hamstrings | músculo: hamstrings; músculo: abdominals; músculo: glutes; músculo: lower back; patrón: snatch |
| `Hang_Snatch_-_Below_Knees` | Hang Snatch - Below Knees | hamstrings | músculo: hamstrings; músculo: abdominals; músculo: glutes; músculo: lower back; patrón: snatch |
| `Hanging_Bar_Good_Morning` | Hanging Bar Good Morning | hamstrings | músculo: hamstrings; músculo: abdominals; músculo: glutes; músculo: lower back; patrón: good morning; patrón: hanging |
| `Hanging_Leg_Raise` | Hanging Leg Raise | abdominals | músculo: abdominals; patrón: leg raise; patrón: hanging |
| `Hanging_Pike` | Hanging Pike | abdominals | músculo: abdominals; patrón: hanging |
| `Heaving_Snatch_Balance` | Heaving Snatch Balance | quadriceps | músculo: abdominals; músculo: glutes; músculo: hamstrings; patrón: snatch |
| `Heavy_Bag_Thrust` | Heavy Bag Thrust | chest | músculo: abdominals; patrón: heavy bag |
| `Hip_Extension_with_Bands` | Hip Extension with Bands | glutes | músculo: glutes; músculo: hamstrings |
| `Hip_Lift_with_Band` | Hip Lift with Band | glutes | músculo: glutes; músculo: hamstrings |
| `Hug_A_Ball` | Hug A Ball | lower back | músculo: lower back; músculo: glutes |
| `Hug_Knees_To_Chest` | Hug Knees To Chest | lower back | músculo: lower back; músculo: glutes |
| `Hurdle_Hops` | Hurdle Hops | hamstrings | músculo: hamstrings; músculo: glutes; patrón: hops |
| `Hyperextensions_Back_Extensions` | Hyperextensions (Back Extensions) | lower back | músculo: lower back; músculo: glutes; músculo: hamstrings; patrón: hyperextension; patrón: back extension; patrón: back |
| `Hyperextensions_With_No_Hyperextension_Bench` | Hyperextensions With No Hyperextension Bench | lower back | músculo: lower back; músculo: glutes; músculo: hamstrings; patrón: hyperextension |
| `Inchworm` | Inchworm | hamstrings | músculo: hamstrings |
| `Incline_Dumbbell_Flyes_-_With_A_Twist` | Incline Dumbbell Flyes - With A Twist | chest | patrón: twist |
| `Incline_Push-Up` | Incline Push-Up | chest | patrón: push up; patrón: pushup |
| `Incline_Push-Up_Close-Grip` | Incline Push-Up Close-Grip | triceps | patrón: push up; patrón: pushup |
| `Incline_Push-Up_Depth_Jump` | Incline Push-Up Depth Jump | chest | patrón: jump; patrón: push up; patrón: pushup |
| `Incline_Push-Up_Medium` | Incline Push-Up Medium | chest | músculo: abdominals; patrón: push up; patrón: pushup |
| `Incline_Push-Up_Reverse_Grip` | Incline Push-Up Reverse Grip | chest | músculo: abdominals; patrón: push up; patrón: pushup |
| `Incline_Push-Up_Wide` | Incline Push-Up Wide | chest | músculo: abdominals; patrón: push up; patrón: pushup |
| `Intermediate_Groin_Stretch` | Intermediate Groin Stretch | hamstrings | músculo: hamstrings |
| `Intermediate_Hip_Flexor_and_Quad_Stretch` | Intermediate Hip Flexor and Quad Stretch | quadriceps | patrón: hip flexor |
| `Internal_Rotation_with_Band` | Internal Rotation with Band | shoulders | patrón: rotation |
| `Inverted_Row` | Inverted Row | middle back | patrón: row |
| `Inverted_Row_with_Straps` | Inverted Row with Straps | middle back | patrón: row |
| `Iron_Cross` | Iron Cross | shoulders | músculo: glutes; músculo: hamstrings; músculo: lower back |
| `Iron_Crosses_stretch` | Iron Crosses (stretch) | quadriceps | patrón: iron crosses |
| `Isometric_Neck_Exercise_-_Front_And_Back` | Isometric Neck Exercise - Front And Back | neck | patrón: back |
| `Isometric_Wipers` | Isometric Wipers | chest | músculo: abdominals |
| `Jackknife_Sit-Up` | Jackknife Sit-Up | abdominals | músculo: abdominals; patrón: sit up; patrón: situp; patrón: jackknife |
| `Janda_Sit-Up` | Janda Sit-Up | abdominals | músculo: abdominals; patrón: sit up; patrón: situp |
| `Jefferson_Squats` | Jefferson Squats | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: squat |
| `Jerk_Balance` | Jerk Balance | shoulders | músculo: glutes; músculo: hamstrings; patrón: jerk |
| `Jerk_Dip_Squat` | Jerk Dip Squat | quadriceps | músculo: abdominals; patrón: jerk; patrón: squat |
| `Jogging_Treadmill` | Jogging, Treadmill | quadriceps | músculo: glutes; músculo: hamstrings; patrón: jog |
| `Keg_Load` | Keg Load | lower back | músculo: lower back; músculo: abdominals; músculo: glutes; músculo: hamstrings; patrón: keg |
| `Kettlebell_Arnold_Press` | Kettlebell Arnold Press | shoulders | patrón: kettlebell; patrón: arnold |
| `Kettlebell_Dead_Clean` | Kettlebell Dead Clean | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: clean; patrón: kettlebell |
| `Kettlebell_Figure_8` | Kettlebell Figure 8 | abdominals | músculo: abdominals; músculo: hamstrings; patrón: figure 8; patrón: kettlebell |
| `Kettlebell_Halo` | Kettlebell Halo | shoulders | músculo: abdominals; patrón: kettlebell |
| `Kettlebell_Halo_With_Overhead_Extension` | Kettlebell Halo with Overhead Extension | shoulders | músculo: abdominals; patrón: overhead; patrón: kettlebell |
| `Kettlebell_Hang_Clean` | Kettlebell Hang Clean | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: clean; patrón: kettlebell |
| `Kettlebell_One-Legged_Deadlift` | Kettlebell One-Legged Deadlift | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: deadlift; patrón: kettlebell |
| `Kettlebell_Overhead_Triceps_Extension` | Kettlebell Overhead Triceps Extension | triceps | músculo: abdominals; patrón: overhead; patrón: kettlebell |
| `Kettlebell_Pass_Between_The_Legs` | Kettlebell Pass Between The Legs | abdominals | músculo: abdominals; músculo: glutes; músculo: hamstrings; patrón: pass between; patrón: kettlebell |
| `Kettlebell_Pirate_Ships` | Kettlebell Pirate Ships | shoulders | músculo: abdominals; patrón: kettlebell |
| `Kettlebell_Pistol_Squat` | Kettlebell Pistol Squat | quadriceps | músculo: glutes; músculo: hamstrings; patrón: squat; patrón: kettlebell |
| `Kettlebell_Seated_Press` | Kettlebell Seated Press | shoulders | patrón: kettlebell |
| `Kettlebell_Seesaw_Press` | Kettlebell Seesaw Press | shoulders | patrón: kettlebell; patrón: seesaw; patrón: see saw |
| `Kettlebell_Sumo_High_Pull` | Kettlebell Sumo High Pull | traps | músculo: glutes; músculo: hamstrings; patrón: high pull; patrón: kettlebell |
| `Kettlebell_Thruster` | Kettlebell Thruster | shoulders | patrón: thruster; patrón: kettlebell |
| `Kettlebell_Turkish_Get-Up_Lunge_style` | Kettlebell Turkish Get-Up (Lunge style) | shoulders | músculo: abdominals; músculo: hamstrings; patrón: lunge; patrón: kettlebell |
| `Kettlebell_Turkish_Get-Up_Squat_style` | Kettlebell Turkish Get-Up (Squat style) | shoulders | músculo: abdominals; músculo: hamstrings; patrón: squat; patrón: kettlebell |
| `Kettlebell_Windmill` | Kettlebell Windmill | abdominals | músculo: abdominals; músculo: glutes; músculo: hamstrings; patrón: windmill; patrón: kettlebell |
| `Kipping_Muscle_Up` | Kipping Muscle Up | lats | músculo: abdominals; patrón: muscle up; patrón: kipping |
| `Knee_Across_The_Body` | Knee Across The Body | glutes | músculo: glutes; músculo: lower back |
| `Knee_Circles` | Knee Circles | calves | músculo: hamstrings |
| `Knee_Hip_Raise_On_Parallel_Bars` | Knee/Hip Raise On Parallel Bars | abdominals | músculo: abdominals |
| `Knee_Tuck_Jump` | Knee Tuck Jump | hamstrings | músculo: hamstrings; músculo: glutes; patrón: jump |
| `Kneeling_Arm_Drill` | Kneeling Arm Drill | shoulders | músculo: abdominals |
| `Kneeling_Cable_Crunch_With_Alternating_Oblique_Twists` | Kneeling Cable Crunch With Alternating Oblique Twists | abdominals | músculo: abdominals; patrón: crunch; patrón: twist |
| `Kneeling_High_Pulley_Row` | Kneeling High Pulley Row | lats | patrón: high pull; patrón: row |
| `Kneeling_Hip_Flexor` | Kneeling Hip Flexor | quadriceps | patrón: hip flexor |
| `Kneeling_Jump_Squat` | Kneeling Jump Squat | glutes | músculo: glutes; músculo: hamstrings; patrón: squat; patrón: jump |
| `Kneeling_Single-Arm_High_Pulley_Row` | Kneeling Single-Arm High Pulley Row | lats | patrón: high pull; patrón: row |
| `Kneeling_Squat` | Kneeling Squat | glutes | músculo: glutes; músculo: abdominals; músculo: hamstrings; músculo: lower back; patrón: squat |
| `Landmine_180s` | Landmine 180's | abdominals | músculo: abdominals; músculo: glutes; músculo: lower back; patrón: landmine |
| `Landmine_Linear_Jammer` | Landmine Linear Jammer | shoulders | músculo: abdominals; músculo: hamstrings; patrón: landmine; patrón: jammer |
| `Lateral_Bound` | Lateral Bound | adductors | músculo: glutes; músculo: hamstrings; patrón: bound |
| `Lateral_Box_Jump` | Lateral Box Jump | adductors | músculo: glutes; músculo: hamstrings; patrón: jump; patrón: box |
| `Lateral_Cone_Hops` | Lateral Cone Hops | adductors | músculo: glutes; músculo: hamstrings; patrón: hops |
| `Leg-Up_Hamstring_Stretch` | Leg-Up Hamstring Stretch | hamstrings | músculo: hamstrings |
| `Leg_Lift` | Leg Lift | glutes | músculo: glutes; músculo: hamstrings |
| `Leg_Press` | Leg Press | quadriceps | músculo: glutes; músculo: hamstrings; patrón: leg press |
| `Leg_Pull-In` | Leg Pull-In | abdominals | músculo: abdominals |
| `Leverage_Deadlift` | Leverage Deadlift | quadriceps | músculo: glutes; músculo: hamstrings; patrón: deadlift |
| `Leverage_High_Row` | Leverage High Row | middle back | patrón: row |
| `Leverage_Iso_Row` | Leverage Iso Row | lats | patrón: row |
| `Leverage_Shoulder_Press` | Leverage Shoulder Press | shoulders | patrón: shoulder press |
| `Leverage_Shrug` | Leverage Shrug | traps | patrón: shrug |
| `Linear_3-Part_Start_Technique` | Linear 3-Part Start Technique | hamstrings | músculo: hamstrings |
| `Linear_Acceleration_Wall_Drill` | Linear Acceleration Wall Drill | hamstrings | músculo: hamstrings; músculo: glutes |
| `Linear_Depth_Jump` | Linear Depth Jump | quadriceps | músculo: glutes; músculo: hamstrings; patrón: jump |
| `Log_Lift` | Log Lift | shoulders | músculo: abdominals; músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: log lift |
| `London_Bridges` | London Bridges | lats | patrón: bridge |
| `Looking_At_Ceiling` | Looking At Ceiling | quadriceps | patrón: looking at ceiling |
| `Low_Pulley_Row_To_Neck` | Low Pulley Row To Neck | shoulders | patrón: row |
| `Lower_Back-SMR` | Lower Back-SMR | lower back | músculo: lower back; patrón: back |
| `Lower_Back_Curl` | Lower Back Curl | abdominals | músculo: abdominals; patrón: back |
| `Lunge_Pass_Through` | Lunge Pass Through | hamstrings | músculo: hamstrings; músculo: glutes; patrón: lunge |
| `Lunge_Sprint` | Lunge Sprint | quadriceps | músculo: glutes; músculo: hamstrings; patrón: lunge; patrón: sprint |
| `Lying_Cambered_Barbell_Row` | Lying Cambered Barbell Row | middle back | patrón: row |
| `Lying_Close-Grip_Bar_Curl_On_High_Pulley` | Lying Close-Grip Bar Curl On High Pulley | biceps | patrón: high pull |
| `Lying_Crossover` | Lying Crossover | abductors | patrón: lying crossover |
| `Lying_Face_Down_Plate_Neck_Resistance` | Lying Face Down Plate Neck Resistance | neck | patrón: stance |
| `Lying_Face_Up_Plate_Neck_Resistance` | Lying Face Up Plate Neck Resistance | neck | patrón: stance |
| `Lying_Glute` | Lying Glute | glutes | músculo: glutes |
| `Lying_Hamstring` | Lying Hamstring | hamstrings | músculo: hamstrings |
| `Lying_Leg_Curls` | Lying Leg Curls | hamstrings | músculo: hamstrings |
| `Lying_Machine_Squat` | Lying Machine Squat | quadriceps | músculo: glutes; músculo: hamstrings; patrón: squat |
| `Lying_T-Bar_Row` | Lying T-Bar Row | middle back | patrón: row |
| `Machine_Bench_Press` | Machine Bench Press | chest | patrón: bench press |
| `Machine_Shoulder_Military_Press` | Machine Shoulder (Military) Press | shoulders | patrón: military |
| `Medicine_Ball_Chest_Pass` | Medicine Ball Chest Pass | chest | patrón: medicine ball |
| `Medicine_Ball_Full_Twist` | Medicine Ball Full Twist | abdominals | músculo: abdominals; patrón: twist; patrón: medicine ball |
| `Medicine_Ball_Scoop_Throw` | Medicine Ball Scoop Throw | shoulders | músculo: abdominals; músculo: hamstrings; patrón: row; patrón: throw; patrón: medicine ball |
| `Middle_Back_Shrug` | Middle Back Shrug | middle back | patrón: shrug; patrón: back |
| `Middle_Back_Stretch` | Middle Back Stretch | middle back | músculo: abdominals; músculo: lower back; patrón: back |
| `Monster_Walk` | Monster Walk | abductors | patrón: monster walk |
| `Mountain_Climbers` | Mountain Climbers | quadriceps | músculo: hamstrings; patrón: mountain climber |
| `Moving_Claw_Series` | Moving Claw Series | hamstrings | músculo: hamstrings |
| `Muscle_Snatch` | Muscle Snatch | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: snatch |
| `Muscle_Up` | Muscle Up | lats | músculo: abdominals; patrón: muscle up |
| `Narrow_Stance_Hack_Squats` | Narrow Stance Hack Squats | quadriceps | músculo: glutes; músculo: hamstrings; patrón: squat; patrón: row; patrón: stance |
| `Narrow_Stance_Leg_Press` | Narrow Stance Leg Press | quadriceps | músculo: glutes; músculo: hamstrings; patrón: leg press; patrón: row; patrón: stance |
| `Narrow_Stance_Squats` | Narrow Stance Squats | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: squat; patrón: row; patrón: stance |
| `Natural_Glute_Ham_Raise` | Natural Glute Ham Raise | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back |
| `Oblique_Crunches` | Oblique Crunches | abdominals | músculo: abdominals; patrón: crunch |
| `Oblique_Crunches_-_On_The_Floor` | Oblique Crunches - On The Floor | abdominals | músculo: abdominals; patrón: crunch |
| `Olympic_Squat` | Olympic Squat | quadriceps | músculo: glutes; músculo: hamstrings; patrón: squat |
| `On-Your-Back_Quad_Stretch` | On-Your-Back Quad Stretch | quadriceps | patrón: back |
| `One-Arm_Dumbbell_Row` | One-Arm Dumbbell Row | middle back | patrón: row |
| `One-Arm_High-Pulley_Cable_Side_Bends` | One-Arm High-Pulley Cable Side Bends | abdominals | músculo: abdominals; patrón: high pull; patrón: side bend |
| `One-Arm_Kettlebell_Clean` | One-Arm Kettlebell Clean | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: clean; patrón: kettlebell |
| `One-Arm_Kettlebell_Clean_and_Jerk` | One-Arm Kettlebell Clean and Jerk | shoulders | patrón: clean; patrón: jerk; patrón: kettlebell |
| `One-Arm_Kettlebell_Floor_Press` | One-Arm Kettlebell Floor Press | chest | patrón: kettlebell |
| `One-Arm_Kettlebell_Jerk` | One-Arm Kettlebell Jerk | shoulders | patrón: jerk; patrón: kettlebell |
| `One-Arm_Kettlebell_Military_Press_To_The_Side` | One-Arm Kettlebell Military Press To The Side | shoulders | patrón: military; patrón: kettlebell |
| `One-Arm_Kettlebell_Para_Press` | One-Arm Kettlebell Para Press | shoulders | patrón: kettlebell; patrón: para press |
| `One-Arm_Kettlebell_Push_Press` | One-Arm Kettlebell Push Press | shoulders | patrón: push press; patrón: kettlebell |
| `One-Arm_Kettlebell_Row` | One-Arm Kettlebell Row | middle back | patrón: row; patrón: kettlebell |
| `One-Arm_Kettlebell_Snatch` | One-Arm Kettlebell Snatch | shoulders | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: snatch; patrón: kettlebell |
| `One-Arm_Kettlebell_Split_Jerk` | One-Arm Kettlebell Split Jerk | shoulders | músculo: glutes; músculo: hamstrings; patrón: jerk; patrón: kettlebell |
| `One-Arm_Kettlebell_Split_Snatch` | One-Arm Kettlebell Split Snatch | shoulders | músculo: hamstrings; patrón: snatch; patrón: kettlebell |
| `One-Arm_Kettlebell_Swings` | One-Arm Kettlebell Swings | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: swing; patrón: kettlebell |
| `One-Arm_Long_Bar_Row` | One-Arm Long Bar Row | middle back | patrón: row |
| `One-Arm_Medicine_Ball_Slam` | One-Arm Medicine Ball Slam | abdominals | músculo: abdominals; patrón: slam; patrón: medicine ball |
| `One-Arm_Open_Palm_Kettlebell_Clean` | One-Arm Open Palm Kettlebell Clean | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: clean; patrón: kettlebell |
| `One-Arm_Overhead_Kettlebell_Squats` | One-Arm Overhead Kettlebell Squats | quadriceps | músculo: glutes; músculo: hamstrings; patrón: squat; patrón: overhead; patrón: kettlebell |
| `One-Arm_Side_Deadlift` | One-Arm Side Deadlift | quadriceps | músculo: abdominals; músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: deadlift |
| `One-Legged_Cable_Kickback` | One-Legged Cable Kickback | glutes | músculo: glutes; músculo: hamstrings; patrón: back |
| `One_Arm_Dumbbell_Bench_Press` | One Arm Dumbbell Bench Press | chest | patrón: bench press |
| `One_Half_Locust` | One Half Locust | quadriceps | músculo: abdominals; patrón: locust |
| `One_Knee_To_Chest` | One Knee To Chest | glutes | músculo: glutes; músculo: hamstrings; músculo: lower back |
| `One_Leg_Barbell_Squat` | One Leg Barbell Squat | quadriceps | músculo: glutes; músculo: hamstrings; patrón: squat |
| `Open_Palm_Kettlebell_Clean` | Open Palm Kettlebell Clean | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: clean; patrón: kettlebell |
| `Otis-Up` | Otis-Up | abdominals | músculo: abdominals |
| `Overhead_Cable_Curl` | Overhead Cable Curl | biceps | patrón: overhead |
| `Overhead_Lat` | Overhead Lat | lats | patrón: overhead |
| `Overhead_Slam` | Overhead Slam | lats | patrón: overhead; patrón: slam |
| `Overhead_Squat` | Overhead Squat | quadriceps | músculo: abdominals; músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: squat; patrón: overhead |
| `Overhead_Stretch` | Overhead Stretch | abdominals | músculo: abdominals; patrón: overhead |
| `Overhead_Triceps` | Overhead Triceps | triceps | patrón: overhead |
| `Pallof_Press` | Pallof Press | abdominals | músculo: abdominals |
| `Pallof_Press_With_Rotation` | Pallof Press With Rotation | abdominals | músculo: abdominals; patrón: rotation |
| `Pelvic_Tilt_Into_Bridge` | Pelvic Tilt Into Bridge | lower back | músculo: lower back; patrón: bridge |
| `Physioball_Hip_Bridge` | Physioball Hip Bridge | glutes | músculo: glutes; músculo: hamstrings; patrón: bridge |
| `Pin_Presses` | Pin Presses | triceps | patrón: pin press |
| `Piriformis-SMR` | Piriformis-SMR | glutes | músculo: glutes |
| `Plank` | Plank | abdominals | músculo: abdominals |
| `Plate_Twist` | Plate Twist | abdominals | músculo: abdominals; patrón: twist |
| `Platform_Hamstring_Slides` | Platform Hamstring Slides | hamstrings | músculo: hamstrings; músculo: glutes |
| `Plie_Dumbbell_Squat` | Plie Dumbbell Squat | quadriceps | músculo: abdominals; músculo: glutes; músculo: hamstrings; patrón: squat |
| `Plyo_Kettlebell_Pushups` | Plyo Kettlebell Pushups | chest | patrón: yoke; patrón: kettlebell; patrón: push up; patrón: pushup; patrón: plyo |
| `Plyo_Push-up` | Plyo Push-up | chest | patrón: push up; patrón: pushup; patrón: plyo |
| `Power_Clean` | Power Clean | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: clean |
| `Power_Clean_from_Blocks` | Power Clean from Blocks | hamstrings | músculo: hamstrings; patrón: clean |
| `Power_Jerk` | Power Jerk | quadriceps | músculo: abdominals; músculo: glutes; músculo: hamstrings; patrón: jerk |
| `Power_Partials` | Power Partials | shoulders | patrón: power partials |
| `Power_Snatch` | Power Snatch | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: snatch |
| `Power_Snatch_from_Blocks` | Power Snatch from Blocks | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: snatch |
| `Power_Stairs` | Power Stairs | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back |
| `Press_Sit-Up` | Press Sit-Up | abdominals | músculo: abdominals; patrón: sit up; patrón: situp |
| `Prone_Manual_Hamstring` | Prone Manual Hamstring | hamstrings | músculo: hamstrings |
| `Prowler_Sprint` | Prowler Sprint | hamstrings | músculo: hamstrings; músculo: glutes; patrón: row; patrón: sprint |
| `Pull_Through` | Pull Through | glutes | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: pull through |
| `Push-Up_Wide` | Push-Up Wide | chest | músculo: abdominals; patrón: push up; patrón: pushup |
| `Push-Ups_-_Close_Triceps_Position` | Push-Ups - Close Triceps Position | triceps | patrón: push up; patrón: pushup |
| `Push-Ups_With_Feet_Elevated` | Push-Ups With Feet Elevated | chest | patrón: push up; patrón: pushup |
| `Push-Ups_With_Feet_On_An_Exercise_Ball` | Push-Ups With Feet On An Exercise Ball | chest | patrón: push up; patrón: pushup |
| `Push_Press` | Push Press | shoulders | patrón: push press |
| `Push_Press_-_Behind_the_Neck` | Push Press - Behind the Neck | shoulders | patrón: push press |
| `Push_Up_to_Side_Plank` | Push Up to Side Plank | chest | músculo: abdominals; patrón: push up; patrón: pushup |
| `Pushups` | Pushups | chest | patrón: push up; patrón: pushup |
| `Pushups_Close_and_Wide_Hand_Positions` | Pushups (Close and Wide Hand Positions) | chest | patrón: push up; patrón: pushup |
| `Pyramid` | Pyramid | lower back | músculo: lower back |
| `Quick_Leap` | Quick Leap | quadriceps | músculo: hamstrings; patrón: leap |
| `Rack_Delivery` | Rack Delivery | shoulders | patrón: rack delivery |
| `Rack_Pull_with_Bands` | Rack Pull with Bands | lower back | músculo: lower back; músculo: glutes; músculo: hamstrings; patrón: rack pull |
| `Rack_Pulls` | Rack Pulls | lower back | músculo: lower back; músculo: glutes; músculo: hamstrings; patrón: rack pull |
| `Rear_Leg_Raises` | Rear Leg Raises | quadriceps | patrón: leg raise |
| `Recumbent_Bike` | Recumbent Bike | quadriceps | músculo: glutes; músculo: hamstrings; patrón: bike |
| `Return_Push_from_Stance` | Return Push from Stance | shoulders | patrón: stance |
| `Reverse_Band_Bench_Press` | Reverse Band Bench Press | triceps | patrón: bench press |
| `Reverse_Band_Box_Squat` | Reverse Band Box Squat | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: squat; patrón: box |
| `Reverse_Band_Deadlift` | Reverse Band Deadlift | lower back | músculo: lower back; músculo: glutes; músculo: hamstrings; patrón: deadlift |
| `Reverse_Band_Power_Squat` | Reverse Band Power Squat | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: squat |
| `Reverse_Band_Sumo_Deadlift` | Reverse Band Sumo Deadlift | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: deadlift |
| `Reverse_Crunch` | Reverse Crunch | abdominals | músculo: abdominals; patrón: crunch |
| `Reverse_Flyes_With_External_Rotation` | Reverse Flyes With External Rotation | shoulders | patrón: rotation |
| `Reverse_Grip_Bent-Over_Rows` | Reverse Grip Bent-Over Rows | middle back | patrón: bent over; patrón: row |
| `Reverse_Hyperextension` | Reverse Hyperextension | hamstrings | músculo: hamstrings; músculo: glutes; patrón: hyperextension |
| `Reverse_Triceps_Bench_Press` | Reverse Triceps Bench Press | triceps | patrón: bench press |
| `Rickshaw_Carry` | Rickshaw Carry | forearms | músculo: abdominals; músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: rickshaw |
| `Rickshaw_Deadlift` | Rickshaw Deadlift | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: deadlift; patrón: rickshaw |
| `Rocket_Jump` | Rocket Jump | quadriceps | músculo: hamstrings; patrón: jump |
| `Rocking_Standing_Calf_Raise` | Rocking Standing Calf Raise | calves | patrón: standing; patrón: calf raise |
| `Romanian_Deadlift` | Romanian Deadlift | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: deadlift; patrón: romanian |
| `Romanian_Deadlift_from_Deficit` | Romanian Deadlift from Deficit | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: deadlift; patrón: romanian |
| `Rope_Climb` | Rope Climb | lats | patrón: rope |
| `Rope_Crunch` | Rope Crunch | abdominals | músculo: abdominals; patrón: crunch; patrón: rope |
| `Rope_Jumping` | Rope Jumping | quadriceps | músculo: hamstrings; patrón: rope; patrón: jump |
| `Rope_Straight-Arm_Pulldown` | Rope Straight-Arm Pulldown | lats | patrón: rope |
| `Rowing_Stationary` | Rowing, Stationary | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: row |
| `Runners_Stretch` | Runner's Stretch | hamstrings | músculo: hamstrings |
| `Running_Treadmill` | Running, Treadmill | quadriceps | músculo: glutes; músculo: hamstrings; patrón: running |
| `Russian_Twist` | Russian Twist | abdominals | músculo: abdominals; músculo: lower back; patrón: twist |
| `Sandbag_Load` | Sandbag Load | quadriceps | músculo: abdominals; músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: sandbag |
| `Scissor_Kick` | Scissor Kick | abdominals | músculo: abdominals |
| `Scissors_Jump` | Scissors Jump | quadriceps | músculo: glutes; músculo: hamstrings; patrón: jump |
| `Seated_Band_Hamstring_Curl` | Seated Band Hamstring Curl | hamstrings | músculo: hamstrings |
| `Seated_Barbell_Military_Press` | Seated Barbell Military Press | shoulders | patrón: military |
| `Seated_Barbell_Twist` | Seated Barbell Twist | abdominals | músculo: abdominals; patrón: twist |
| `Seated_Bent-Over_One-Arm_Dumbbell_Triceps_Extension` | Seated Bent-Over One-Arm Dumbbell Triceps Extension | triceps | patrón: bent over |
| `Seated_Bent-Over_Rear_Delt_Raise` | Seated Bent-Over Rear Delt Raise | shoulders | patrón: bent over |
| `Seated_Bent-Over_Two-Arm_Dumbbell_Triceps_Extension` | Seated Bent-Over Two-Arm Dumbbell Triceps Extension | triceps | patrón: bent over |
| `Seated_Cable_Rows` | Seated Cable Rows | middle back | patrón: row |
| `Seated_Cable_Shoulder_Press` | Seated Cable Shoulder Press | shoulders | patrón: shoulder press |
| `Seated_Calf_Raise` | Seated Calf Raise | calves | patrón: calf raise |
| `Seated_Calf_Stretch` | Seated Calf Stretch | calves | músculo: hamstrings; músculo: lower back |
| `Seated_Dumbbell_Press` | Seated Dumbbell Press | shoulders | patrón: seated dumbbell press |
| `Seated_Flat_Bench_Leg_Pull-In` | Seated Flat Bench Leg Pull-In | abdominals | músculo: abdominals |
| `Seated_Floor_Hamstring_Stretch` | Seated Floor Hamstring Stretch | hamstrings | músculo: hamstrings |
| `Seated_Glute` | Seated Glute | glutes | músculo: glutes |
| `Seated_Good_Mornings` | Seated Good Mornings | lower back | músculo: lower back; músculo: glutes; patrón: good morning |
| `Seated_Hamstring` | Seated Hamstring | hamstrings | músculo: hamstrings |
| `Seated_Hamstring_and_Calf_Stretch` | Seated Hamstring and Calf Stretch | hamstrings | músculo: hamstrings |
| `Seated_Head_Harness_Neck_Resistance` | Seated Head Harness Neck Resistance | neck | patrón: stance |
| `Seated_Leg_Curl` | Seated Leg Curl | hamstrings | músculo: hamstrings |
| `Seated_Leg_Tucks` | Seated Leg Tucks | abdominals | músculo: abdominals |
| `Seated_One-arm_Cable_Pulley_Rows` | Seated One-arm Cable Pulley Rows | middle back | patrón: row |
| `Seated_Overhead_Stretch` | Seated Overhead Stretch | abdominals | músculo: abdominals; patrón: overhead |
| `Seated_Triceps_Press` | Seated Triceps Press | triceps | patrón: seated triceps press |
| `See-Saw_Press_Alternating_Side_Press` | See-Saw Press (Alternating Side Press) | shoulders | músculo: abdominals; patrón: seesaw; patrón: see saw |
| `Shotgun_Row` | Shotgun Row | lats | patrón: row |
| `Shoulder_Press_-_With_Bands` | Shoulder Press - With Bands | shoulders | patrón: shoulder press |
| `Side_Bridge` | Side Bridge | abdominals | músculo: abdominals; patrón: bridge |
| `Side_Hop-Sprint` | Side Hop-Sprint | quadriceps | músculo: hamstrings; patrón: hops; patrón: sprint |
| `Side_Jackknife` | Side Jackknife | abdominals | músculo: abdominals; patrón: jackknife |
| `Side_Leg_Raises` | Side Leg Raises | adductors | patrón: leg raise |
| `Side_Lying_Groin_Stretch` | Side Lying Groin Stretch | adductors | músculo: hamstrings |
| `Side_Standing_Long_Jump` | Side Standing Long Jump | quadriceps | músculo: glutes; músculo: hamstrings; patrón: standing; patrón: jump |
| `Side_to_Side_Box_Shuffle` | Side to Side Box Shuffle | quadriceps | músculo: hamstrings; patrón: box |
| `Single-Arm_Linear_Jammer` | Single-Arm Linear Jammer | shoulders | patrón: jammer |
| `Single-Arm_Push-Up` | Single-Arm Push-Up | chest | patrón: push up; patrón: pushup |
| `Single-Cone_Sprint_Drill` | Single-Cone Sprint Drill | quadriceps | músculo: glutes; músculo: hamstrings; patrón: sprint |
| `Single-Leg_High_Box_Squat` | Single-Leg High Box Squat | quadriceps | músculo: glutes; músculo: hamstrings; patrón: squat; patrón: box |
| `Single-Leg_Hop_Progression` | Single-Leg Hop Progression | quadriceps | músculo: hamstrings |
| `Single-Leg_Lateral_Hop` | Single-Leg Lateral Hop | quadriceps | músculo: hamstrings |
| `Single-Leg_Stride_Jump` | Single-Leg Stride Jump | quadriceps | músculo: hamstrings; patrón: jump |
| `Single_Leg_Butt_Kick` | Single Leg Butt Kick | quadriceps | músculo: hamstrings |
| `Single_Leg_Glute_Bridge` | Single Leg Glute Bridge | glutes | músculo: glutes; músculo: hamstrings; patrón: bridge |
| `Single_Leg_Push-off` | Single Leg Push-off | quadriceps | músculo: hamstrings |
| `Sit-Up` | Sit-Up | abdominals | músculo: abdominals; patrón: sit up; patrón: situp |
| `Sit_Squats` | Sit Squats | quadriceps | músculo: glutes; músculo: hamstrings; patrón: squat |
| `Skating` | Skating | quadriceps | músculo: glutes; músculo: hamstrings; patrón: skating |
| `Sled_Drag_-_Harness` | Sled Drag - Harness | quadriceps | músculo: glutes; músculo: hamstrings; patrón: sled; patrón: drag |
| `Sled_Overhead_Backward_Walk` | Sled Overhead Backward Walk | shoulders | patrón: overhead; patrón: sled; patrón: back |
| `Sled_Overhead_Triceps_Extension` | Sled Overhead Triceps Extension | triceps | patrón: overhead; patrón: sled |
| `Sled_Push` | Sled Push | quadriceps | músculo: glutes; músculo: hamstrings; patrón: sled |
| `Sled_Reverse_Flye` | Sled Reverse Flye | shoulders | patrón: sled |
| `Sled_Row` | Sled Row | middle back | patrón: row; patrón: sled |
| `Sledgehammer_Swings` | Sledgehammer Swings | abdominals | músculo: abdominals; patrón: swing; patrón: sled |
| `Smith_Machine_Behind_the_Back_Shrug` | Smith Machine Behind the Back Shrug | traps | patrón: shrug; patrón: back |
| `Smith_Machine_Bench_Press` | Smith Machine Bench Press | chest | patrón: bench press |
| `Smith_Machine_Bent_Over_Row` | Smith Machine Bent Over Row | middle back | patrón: bent over; patrón: row |
| `Smith_Machine_Calf_Raise` | Smith Machine Calf Raise | calves | patrón: calf raise |
| `Smith_Machine_Close-Grip_Bench_Press` | Smith Machine Close-Grip Bench Press | triceps | patrón: bench press |
| `Smith_Machine_Hang_Power_Clean` | Smith Machine Hang Power Clean | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: clean |
| `Smith_Machine_Hip_Raise` | Smith Machine Hip Raise | abdominals | músculo: abdominals |
| `Smith_Machine_Incline_Bench_Press` | Smith Machine Incline Bench Press | chest | patrón: bench press |
| `Smith_Machine_Leg_Press` | Smith Machine Leg Press | quadriceps | músculo: glutes; músculo: hamstrings; patrón: leg press |
| `Smith_Machine_One-Arm_Upright_Row` | Smith Machine One-Arm Upright Row | shoulders | patrón: row |
| `Smith_Machine_Overhead_Shoulder_Press` | Smith Machine Overhead Shoulder Press | shoulders | patrón: overhead; patrón: shoulder press |
| `Smith_Machine_Pistol_Squat` | Smith Machine Pistol Squat | quadriceps | músculo: glutes; músculo: hamstrings; patrón: squat |
| `Smith_Machine_Reverse_Calf_Raises` | Smith Machine Reverse Calf Raises | calves | patrón: calf raise |
| `Smith_Machine_Squat` | Smith Machine Squat | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: squat |
| `Smith_Machine_Stiff-Legged_Deadlift` | Smith Machine Stiff-Legged Deadlift | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: deadlift; patrón: stiff leg |
| `Smith_Machine_Upright_Row` | Smith Machine Upright Row | traps | patrón: row |
| `Smith_Single-Leg_Split_Squat` | Smith Single-Leg Split Squat | quadriceps | músculo: glutes; músculo: hamstrings; patrón: squat |
| `Snatch` | Snatch | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: snatch |
| `Snatch_Balance` | Snatch Balance | quadriceps | músculo: glutes; músculo: hamstrings; patrón: snatch |
| `Snatch_Deadlift` | Snatch Deadlift | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: deadlift; patrón: snatch |
| `Snatch_Pull` | Snatch Pull | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: snatch |
| `Snatch_Shrug` | Snatch Shrug | traps | patrón: snatch; patrón: shrug |
| `Snatch_from_Blocks` | Snatch from Blocks | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: snatch |
| `Speed_Band_Overhead_Triceps` | Speed Band Overhead Triceps | triceps | patrón: overhead |
| `Speed_Box_Squat` | Speed Box Squat | quadriceps | músculo: glutes; músculo: hamstrings; patrón: squat; patrón: box |
| `Speed_Squats` | Speed Squats | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: squat |
| `Spell_Caster` | Spell Caster | abdominals | músculo: abdominals; músculo: glutes |
| `Spider_Crawl` | Spider Crawl | abdominals | músculo: abdominals |
| `Spinal_Stretch` | Spinal Stretch | middle back | músculo: lower back |
| `Split_Clean` | Split Clean | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: clean |
| `Split_Jerk` | Split Jerk | quadriceps | músculo: glutes; músculo: hamstrings; patrón: jerk |
| `Split_Jump` | Split Jump | quadriceps | músculo: glutes; músculo: hamstrings; patrón: jump |
| `Split_Snatch` | Split Snatch | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: snatch |
| `Split_Squat_with_Dumbbells` | Split Squat with Dumbbells | quadriceps | músculo: glutes; músculo: hamstrings; patrón: squat |
| `Split_Squats` | Split Squats | hamstrings | músculo: hamstrings; músculo: glutes; patrón: squat |
| `Squat_Jerk` | Squat Jerk | quadriceps | músculo: glutes; músculo: hamstrings; patrón: jerk; patrón: squat |
| `Squat_with_Bands` | Squat with Bands | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: squat |
| `Squat_with_Chains` | Squat with Chains | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: squat |
| `Squat_with_Plate_Movers` | Squat with Plate Movers | quadriceps | músculo: glutes; músculo: hamstrings; patrón: squat |
| `Squats_-_With_Bands` | Squats - With Bands | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: squat |
| `Stairmaster` | Stairmaster | quadriceps | músculo: glutes; músculo: hamstrings |
| `Standing_Alternating_Dumbbell_Press` | Standing Alternating Dumbbell Press | shoulders | patrón: standing |
| `Standing_Barbell_Calf_Raise` | Standing Barbell Calf Raise | calves | patrón: standing; patrón: calf raise |
| `Standing_Barbell_Press_Behind_Neck` | Standing Barbell Press Behind Neck | shoulders | patrón: standing |
| `Standing_Bent-Over_One-Arm_Dumbbell_Triceps_Extension` | Standing Bent-Over One-Arm Dumbbell Triceps Extension | triceps | patrón: bent over; patrón: standing |
| `Standing_Bent-Over_Two-Arm_Dumbbell_Triceps_Extension` | Standing Bent-Over Two-Arm Dumbbell Triceps Extension | triceps | patrón: bent over; patrón: standing |
| `Standing_Biceps_Cable_Curl` | Standing Biceps Cable Curl | biceps | patrón: standing |
| `Standing_Biceps_Stretch` | Standing Biceps Stretch | biceps | patrón: standing |
| `Standing_Bradford_Press` | Standing Bradford Press | shoulders | patrón: standing; patrón: bradford |
| `Standing_Cable_Chest_Press` | Standing Cable Chest Press | chest | patrón: standing |
| `Standing_Cable_Lift` | Standing Cable Lift | abdominals | músculo: abdominals; patrón: standing |
| `Standing_Cable_Wood_Chop` | Standing Cable Wood Chop | abdominals | músculo: abdominals; patrón: standing; patrón: wood chop; patrón: woodchop |
| `Standing_Calf_Raises` | Standing Calf Raises | calves | patrón: standing; patrón: calf raise |
| `Standing_Concentration_Curl` | Standing Concentration Curl | biceps | patrón: standing |
| `Standing_Dumbbell_Calf_Raise` | Standing Dumbbell Calf Raise | calves | patrón: standing; patrón: calf raise |
| `Standing_Dumbbell_Press` | Standing Dumbbell Press | shoulders | patrón: standing |
| `Standing_Dumbbell_Reverse_Curl` | Standing Dumbbell Reverse Curl | biceps | patrón: standing |
| `Standing_Dumbbell_Straight-Arm_Front_Delt_Raise_Above_Head` | Standing Dumbbell Straight-Arm Front Delt Raise Above Head | shoulders | patrón: standing |
| `Standing_Dumbbell_Triceps_Extension` | Standing Dumbbell Triceps Extension | triceps | patrón: standing |
| `Standing_Dumbbell_Upright_Row` | Standing Dumbbell Upright Row | traps | patrón: row; patrón: standing |
| `Standing_Elevated_Quad_Stretch` | Standing Elevated Quad Stretch | quadriceps | patrón: standing |
| `Standing_Front_Barbell_Raise_Over_Head` | Standing Front Barbell Raise Over Head | shoulders | patrón: overhead; patrón: standing |
| `Standing_Gastrocnemius_Calf_Stretch` | Standing Gastrocnemius Calf Stretch | calves | músculo: hamstrings; patrón: standing |
| `Standing_Hamstring_and_Calf_Stretch` | Standing Hamstring and Calf Stretch | hamstrings | músculo: hamstrings; patrón: standing |
| `Standing_Hip_Circles` | Standing Hip Circles | abductors | patrón: standing |
| `Standing_Hip_Flexors` | Standing Hip Flexors | quadriceps | patrón: standing; patrón: hip flexor |
| `Standing_Inner-Biceps_Curl` | Standing Inner-Biceps Curl | biceps | patrón: standing |
| `Standing_Lateral_Stretch` | Standing Lateral Stretch | abdominals | músculo: abdominals; patrón: standing |
| `Standing_Leg_Curl` | Standing Leg Curl | hamstrings | músculo: hamstrings; patrón: standing |
| `Standing_Long_Jump` | Standing Long Jump | quadriceps | músculo: glutes; músculo: hamstrings; patrón: standing; patrón: jump |
| `Standing_Low-Pulley_Deltoid_Raise` | Standing Low-Pulley Deltoid Raise | shoulders | patrón: standing |
| `Standing_Low-Pulley_One-Arm_Triceps_Extension` | Standing Low-Pulley One-Arm Triceps Extension | triceps | patrón: standing |
| `Standing_Military_Press` | Standing Military Press | shoulders | patrón: military; patrón: standing |
| `Standing_Olympic_Plate_Hand_Squeeze` | Standing Olympic Plate Hand Squeeze | forearms | patrón: standing |
| `Standing_One-Arm_Cable_Curl` | Standing One-Arm Cable Curl | biceps | patrón: standing |
| `Standing_One-Arm_Dumbbell_Curl_Over_Incline_Bench` | Standing One-Arm Dumbbell Curl Over Incline Bench | biceps | patrón: standing |
| `Standing_One-Arm_Dumbbell_Triceps_Extension` | Standing One-Arm Dumbbell Triceps Extension | triceps | patrón: standing |
| `Standing_Overhead_Barbell_Triceps_Extension` | Standing Overhead Barbell Triceps Extension | triceps | patrón: overhead; patrón: standing |
| `Standing_Palm-In_One-Arm_Dumbbell_Press` | Standing Palm-In One-Arm Dumbbell Press | shoulders | patrón: standing |
| `Standing_Palms-In_Dumbbell_Press` | Standing Palms-In Dumbbell Press | shoulders | patrón: standing |
| `Standing_Palms-Up_Barbell_Behind_The_Back_Wrist_Curl` | Standing Palms-Up Barbell Behind The Back Wrist Curl | forearms | patrón: standing; patrón: back |
| `Standing_Pelvic_Tilt` | Standing Pelvic Tilt | lower back | músculo: lower back; músculo: glutes; patrón: standing |
| `Standing_Rope_Crunch` | Standing Rope Crunch | abdominals | músculo: abdominals; patrón: standing; patrón: crunch; patrón: rope |
| `Standing_Soleus_And_Achilles_Stretch` | Standing Soleus And Achilles Stretch | calves | patrón: standing |
| `Standing_Toe_Touches` | Standing Toe Touches | hamstrings | músculo: hamstrings; patrón: standing |
| `Standing_Towel_Triceps_Extension` | Standing Towel Triceps Extension | triceps | patrón: standing |
| `Standing_Two-Arm_Overhead_Throw` | Standing Two-Arm Overhead Throw | shoulders | patrón: row; patrón: overhead; patrón: standing; patrón: throw |
| `Star_Jump` | Star Jump | quadriceps | músculo: glutes; músculo: hamstrings; patrón: jump |
| `Step-up_with_Knee_Raise` | Step-up with Knee Raise | glutes | músculo: glutes; músculo: hamstrings; patrón: step up; patrón: stepup |
| `Step_Mill` | Step Mill | quadriceps | músculo: glutes; músculo: hamstrings |
| `Stiff-Legged_Barbell_Deadlift` | Stiff-Legged Barbell Deadlift | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: deadlift; patrón: stiff leg |
| `Stiff-Legged_Dumbbell_Deadlift` | Stiff-Legged Dumbbell Deadlift | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: deadlift; patrón: stiff leg |
| `Stiff_Leg_Barbell_Good_Morning` | Stiff Leg Barbell Good Morning | lower back | músculo: lower back; músculo: glutes; músculo: hamstrings; patrón: good morning; patrón: stiff leg |
| `Stomach_Vacuum` | Stomach Vacuum | abdominals | músculo: abdominals |
| `Straight-Arm_Dumbbell_Pullover` | Straight-Arm Dumbbell Pullover | chest | patrón: pullover |
| `Straight_Bar_Bench_Mid_Rows` | Straight Bar Bench Mid Rows | middle back | patrón: row |
| `Stride_Jump_Crossover` | Stride Jump Crossover | quadriceps | músculo: hamstrings; patrón: jump |
| `Sumo_Deadlift` | Sumo Deadlift | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: deadlift |
| `Sumo_Deadlift_with_Bands` | Sumo Deadlift with Bands | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: deadlift |
| `Sumo_Deadlift_with_Chains` | Sumo Deadlift with Chains | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: deadlift |
| `Superman` | Superman | lower back | músculo: lower back; músculo: glutes; músculo: hamstrings; patrón: superman |
| `Supine_Chest_Throw` | Supine Chest Throw | triceps | patrón: row; patrón: throw |
| `Supine_One-Arm_Overhead_Throw` | Supine One-Arm Overhead Throw | abdominals | músculo: abdominals; patrón: row; patrón: overhead; patrón: throw |
| `Supine_Two-Arm_Overhead_Throw` | Supine Two-Arm Overhead Throw | abdominals | músculo: abdominals; patrón: row; patrón: overhead; patrón: throw |
| `Suspended_Fallout` | Suspended Fallout | abdominals | músculo: abdominals; músculo: lower back; patrón: fallout |
| `Suspended_Push-Up` | Suspended Push-Up | chest | patrón: push up; patrón: pushup |
| `Suspended_Reverse_Crunch` | Suspended Reverse Crunch | abdominals | músculo: abdominals; patrón: crunch |
| `Suspended_Row` | Suspended Row | middle back | patrón: row |
| `Suspended_Split_Squat` | Suspended Split Squat | quadriceps | músculo: glutes; músculo: hamstrings; patrón: squat |
| `T-Bar_Row_with_Handle` | T-Bar Row with Handle | middle back | patrón: row |
| `The_Straddle` | The Straddle | hamstrings | músculo: hamstrings |
| `Thigh_Abductor` | Thigh Abductor | abductors | músculo: glutes |
| `Thigh_Adductor` | Thigh Adductor | adductors | músculo: glutes; músculo: hamstrings |
| `Tire_Flip` | Tire Flip | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: tire flip |
| `Toe_Touchers` | Toe Touchers | abdominals | músculo: abdominals |
| `Torso_Rotation` | Torso Rotation | abdominals | músculo: abdominals; patrón: rotation |
| `Trail_Running_Walking` | Trail Running/Walking | quadriceps | músculo: glutes; músculo: hamstrings; patrón: running |
| `Trap_Bar_Deadlift` | Trap Bar Deadlift | quadriceps | músculo: glutes; músculo: hamstrings; patrón: deadlift |
| `Tricep_Dumbbell_Kickback` | Tricep Dumbbell Kickback | triceps | patrón: back |
| `Triceps_Overhead_Extension_with_Rope` | Triceps Overhead Extension with Rope | triceps | patrón: overhead; patrón: rope |
| `Triceps_Pushdown_-_Rope_Attachment` | Triceps Pushdown - Rope Attachment | triceps | patrón: rope |
| `Tuck_Crunch` | Tuck Crunch | abdominals | músculo: abdominals; patrón: crunch |
| `Two-Arm_Kettlebell_Clean` | Two-Arm Kettlebell Clean | shoulders | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: clean; patrón: kettlebell |
| `Two-Arm_Kettlebell_Jerk` | Two-Arm Kettlebell Jerk | shoulders | patrón: jerk; patrón: kettlebell |
| `Two-Arm_Kettlebell_Military_Press` | Two-Arm Kettlebell Military Press | shoulders | patrón: military; patrón: kettlebell |
| `Two-Arm_Kettlebell_Row` | Two-Arm Kettlebell Row | middle back | patrón: row; patrón: kettlebell |
| `Upper_Back-Leg_Grab` | Upper Back-Leg Grab | hamstrings | músculo: hamstrings; músculo: lower back; patrón: back |
| `Upper_Back_Stretch` | Upper Back Stretch | middle back | patrón: back |
| `Upright_Barbell_Row` | Upright Barbell Row | shoulders | patrón: row |
| `Upright_Cable_Row` | Upright Cable Row | traps | patrón: row |
| `Upright_Row_-_With_Bands` | Upright Row - With Bands | traps | patrón: row |
| `Vertical_Swing` | Vertical Swing | hamstrings | músculo: hamstrings; músculo: glutes; patrón: swing |
| `Walking_Treadmill` | Walking, Treadmill | quadriceps | músculo: glutes; músculo: hamstrings |
| `Weighted_Ball_Hyperextension` | Weighted Ball Hyperextension | lower back | músculo: lower back; músculo: glutes; músculo: hamstrings; patrón: hyperextension |
| `Weighted_Ball_Side_Bend` | Weighted Ball Side Bend | abdominals | músculo: abdominals; patrón: side bend |
| `Weighted_Crunches` | Weighted Crunches | abdominals | músculo: abdominals; patrón: crunch |
| `Weighted_Jump_Squat` | Weighted Jump Squat | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: squat; patrón: jump |
| `Weighted_Sissy_Squat` | Weighted Sissy Squat | quadriceps | músculo: glutes; músculo: hamstrings; patrón: squat |
| `Weighted_Sit-Ups_-_With_Bands` | Weighted Sit-Ups - With Bands | abdominals | músculo: abdominals; patrón: sit up; patrón: situp |
| `Weighted_Squat` | Weighted Squat | quadriceps | músculo: glutes; músculo: hamstrings; patrón: squat |
| `Wide-Grip_Barbell_Bench_Press` | Wide-Grip Barbell Bench Press | chest | patrón: bench press |
| `Wide-Grip_Decline_Barbell_Bench_Press` | Wide-Grip Decline Barbell Bench Press | chest | patrón: bench press |
| `Wide-Grip_Decline_Barbell_Pullover` | Wide-Grip Decline Barbell Pullover | chest | patrón: pullover |
| `Wide-Grip_Standing_Barbell_Curl` | Wide-Grip Standing Barbell Curl | biceps | patrón: standing |
| `Wide_Stance_Barbell_Squat` | Wide Stance Barbell Squat | quadriceps | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: squat; patrón: stance |
| `Wide_Stance_Stiff_Legs` | Wide Stance Stiff Legs | hamstrings | músculo: hamstrings; músculo: glutes; músculo: lower back; patrón: stiff leg; patrón: stance |
| `Wind_Sprints` | Wind Sprints | abdominals | músculo: abdominals; patrón: sprint |
| `Windmills` | Windmills | abductors | músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: windmill |
| `Worlds_Greatest_Stretch` | World's Greatest Stretch | hamstrings | músculo: hamstrings; músculo: glutes |
| `Wrist_Rotations_with_Straight_Bar` | Wrist Rotations with Straight Bar | forearms | patrón: rotation |
| `Yoke_Walk` | Yoke Walk | quadriceps | músculo: abdominals; músculo: glutes; músculo: hamstrings; músculo: lower back; patrón: yoke |
| `Zercher_Squats` | Zercher Squats | quadriceps | músculo: glutes; músculo: hamstrings; patrón: squat |
