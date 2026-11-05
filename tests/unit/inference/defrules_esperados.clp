(defrule R01-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo DOLOR_CABEZA))
  (not (condicion))
  =>
  (assert (disparo (regla-id 1))))

(defrule R02-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo FIEBRE))
  (not (condicion))
  =>
  (assert (disparo (regla-id 2))))

(defrule R03-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo DOLOR_MUSCULAR))
  (not (condicion))
  =>
  (assert (disparo (regla-id 3))))

(defrule R04-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo DOLOR_DENTAL))
  (not (condicion))
  =>
  (assert (disparo (regla-id 4))))

(defrule R05-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo DOLOR_ABDOMINAL))
  (not (condicion))
  =>
  (assert (disparo (regla-id 5))))

(defrule R06-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo FIEBRE))
  (sintoma (codigo MOLESTIAS_RESPIRATORIAS))
  (not (condicion))
  =>
  (assert (disparo (regla-id 6))))

(defrule R07-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo DOLOR_CABEZA))
  (sintoma (codigo FIEBRE))
  (not (condicion))
  =>
  (assert (disparo (regla-id 7))))

(defrule R08-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo DOLOR_MUSCULAR))
  (sintoma (codigo FIEBRE))
  (not (condicion))
  =>
  (assert (disparo (regla-id 8))))

(defrule R09-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo DOLOR_CABEZA))
  (condicion (codigo HIPERTENSION))
  =>
  (assert (disparo (regla-id 9))))

(defrule R10-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo DOLOR_CABEZA))
  (condicion (codigo EMBARAZO))
  =>
  (assert (disparo (regla-id 10))))

(defrule R11-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo FIEBRE))
  (condicion (codigo EMBARAZO))
  =>
  (assert (disparo (regla-id 11))))

(defrule R12-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo DOLOR_MUSCULAR))
  (condicion (codigo ADULTO_MAYOR))
  =>
  (assert (disparo (regla-id 12))))

(defrule R13-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo DOLOR_ABDOMINAL))
  (sintoma (codigo FIEBRE))
  (not (condicion))
  =>
  (assert (disparo (regla-id 13))))

(defrule R14-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo FIEBRE))
  (sintoma (codigo MOLESTIAS_RESPIRATORIAS))
  (condicion (codigo USO_ANTIGRIPAL))
  =>
  (assert (disparo (regla-id 14))))

(defrule R15-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo DOLOR_MUSCULAR))
  (condicion (codigo ADULTO_MAYOR))
  (condicion (codigo USO_ASPIRINA))
  =>
  (assert (disparo (regla-id 15))))

(defrule R16-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_DENTAL))
  (not (condicion))
  =>
  (assert (disparo (regla-id 16))))

(defrule R17-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_MUSCULAR))
  (not (condicion))
  =>
  (assert (disparo (regla-id 17))))

(defrule R18-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_CABEZA))
  (not (condicion))
  =>
  (assert (disparo (regla-id 18))))

(defrule R19-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_ABDOMINAL))
  (not (condicion))
  =>
  (assert (disparo (regla-id 19))))

(defrule R20-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_MUSCULAR))
  (sintoma (codigo FIEBRE))
  (not (condicion))
  =>
  (assert (disparo (regla-id 20))))

(defrule R21-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo FIEBRE))
  (sintoma (codigo MOLESTIAS_RESPIRATORIAS))
  (not (condicion))
  =>
  (assert (disparo (regla-id 21))))

(defrule R22-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_CABEZA))
  (condicion (codigo EMBARAZO))
  =>
  (assert (disparo (regla-id 22))))

(defrule R23-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_MUSCULAR))
  (condicion (codigo HIPERTENSION))
  =>
  (assert (disparo (regla-id 23))))

(defrule R24-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_DENTAL))
  (condicion (codigo DIABETES))
  =>
  (assert (disparo (regla-id 24))))

(defrule R25-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_MUSCULAR))
  (condicion (codigo ADULTO_MAYOR))
  =>
  (assert (disparo (regla-id 25))))

(defrule R26-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_CABEZA))
  (condicion (codigo USO_ANTIGRIPAL))
  =>
  (assert (disparo (regla-id 26))))

(defrule R27-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo FIEBRE))
  (sintoma (codigo MOLESTIAS_RESPIRATORIAS))
  (condicion (codigo USO_ASPIRINA))
  =>
  (assert (disparo (regla-id 27))))

(defrule R28-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_MUSCULAR))
  (condicion (codigo ADULTO_MAYOR))
  (condicion (codigo HIPERTENSION))
  =>
  (assert (disparo (regla-id 28))))

(defrule R29-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_MUSCULAR))
  (condicion (codigo DIABETES))
  (condicion (codigo HIPERTENSION))
  =>
  (assert (disparo (regla-id 29))))

(defrule R30-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_DENTAL))
  (condicion (codigo ADULTO_MAYOR))
  (condicion (codigo OTRO_TRATAMIENTO))
  =>
  (assert (disparo (regla-id 30))))
