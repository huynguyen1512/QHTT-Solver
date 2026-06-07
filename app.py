import streamlit as st
import pandas as pd
import re
from fractions import Fraction

# ==========================================
# CÁC HÀM HỖ TRỢ LATEX VÀ TOÁN HỌC
# ==========================================
def to_latex_frac(val: Fraction):
    """Chuyển đổi Fraction thành chuỗi phân số LaTeX"""
    if val.denominator == 1:
        return str(val.numerator)
    if val.numerator < 0:
        return f"-\\frac{{{-val.numerator}}}{{{val.denominator}}}"
    return f"\\frac{{{val.numerator}}}{{{val.denominator}}}"

def format_term_simple(coef: Fraction, var_name: str, is_first: bool = False):
    """Định dạng số hạng đơn giản cho các bước in Text"""
    if coef == 0: return ""
    sign_str = ""
    if is_first:
        if coef < 0: sign_str = "-"
    else:
        sign_str = " + " if coef > 0 else " - "
    abs_coef = abs(coef)
    coef_str = "" if abs_coef == 1 else to_latex_frac(abs_coef)
    return f"{sign_str}{coef_str}{var_name}"

# ==========================================
# LÕI THUẬT TOÁN ĐƠN HÌNH TỪ VỰNG
# ==========================================
class SimplexDictionary:
    def __init__(self, c_dict, A_dict, b_dict, original_v, method_choice):
        self.N = list(c_dict.keys())
        self.B = list(b_dict.keys())
        self.c = c_dict.copy()
        self.A = {i: A_dict[i].copy() for i in self.B}
        self.b = b_dict.copy()
        self.v = original_v
        
        self.method = method_choice
        self.steps_log = []
        
    def var_sort_key(self, var_str):
        """Hàm sắp xếp biến: x ưu tiên trước w, sau đó sắp xếp theo số tự nhiên"""
        nums = re.findall(r'\d+', var_str)
        num = int(nums[0]) if nums else 0
        prefix_score = 0 if 'x' in var_str else 1
        return (prefix_score, num, var_str)

    def log_auxiliary_problem(self):
        """Xuất quá trình lập bài toán bổ trợ cho Pha 1"""
        latex_str = "### 🔴 Pha 1: Bài toán bổ trợ\n\n"
        
        # BƯỚC 1: Bất phương trình gốc + x_0
        latex_str += "**Bước 1: Lập bài toán bổ trợ (Thêm biến giả $x_0 \\ge 0$ vào các ràng buộc gốc):**\n"
        latex_str += "$$\n\\begin{array}{r l}\n"
        latex_str += "\\min \\partial = & x_0 \\\\\n"
        latex_str += "\\text{với các ràng buộc:} & \\\\\n"

        for i in sorted(self.B, key=self.var_sort_key):
            row_str = ""
            first = True
            for j in sorted(self.N, key=self.var_sort_key):
                coef = self.A[i][j]
                if coef != 0:
                    row_str += format_term_simple(coef, j, is_first=first)
                    first = False

            row_str += format_term_simple(Fraction(-1), "x_0", is_first=first)
            if row_str == "": row_str = "0"
            latex_str += f"& {row_str} \\le {to_latex_frac(self.b[i])} \\\\\n"

        all_vars = sorted(self.N, key=self.var_sort_key) + ["x_0"]
        latex_str += f"& " + ", ".join(all_vars) + " \\ge 0\n"
        latex_str += "\\end{array}\n$$\n"

        # BƯỚC 2: Thêm biến bù w_i
        latex_str += "**Bước 2: Thêm biến bù để chuyển về hệ phương trình:**\n"
        latex_str += "$$\n\\begin{array}{r l}\n"
        latex_str += "\\min \\partial = & x_0 \\\\\n"
        latex_str += "\\text{với các ràng buộc:} & \\\\\n"

        for i in sorted(self.B, key=self.var_sort_key):
            row_str = ""
            first = True
            for j in sorted(self.N, key=self.var_sort_key):
                coef = self.A[i][j]
                if coef != 0:
                    row_str += format_term_simple(coef, j, is_first=first)
                    first = False

            row_str += format_term_simple(Fraction(-1), "x_0", is_first=first)
            row_str += format_term_simple(Fraction(1), i, is_first=False)
            
            if row_str == "": row_str = "0"
            latex_str += f"& {row_str} = {to_latex_frac(self.b[i])} \\\\\n"

        all_vars = sorted(self.N, key=self.var_sort_key) + ["x_0"] + sorted(self.B, key=self.var_sort_key)
        var_chunks = [all_vars[k:k + 8] for k in range(0, len(all_vars), 8)]
        for idx, chunk in enumerate(var_chunks):
            line = ", ".join(chunk)
            if idx == len(var_chunks) - 1:
                latex_str += f"& {line} \\ge 0\n"
            else:
                latex_str += f"& {line}, \\\\\n"

        latex_str += "\\end{array}\n$$\n"
        self.steps_log.append(latex_str)
        
    def log_dictionary(self, title, entering=None, leaving=None, is_phase1=False):
        """Xuất từ vựng: Căn lề thẳng hàng, giãn dòng, và đánh mũi tên chuẩn xác."""
        latex_str = f"**{title}**\n\n"
        
        sorted_N = sorted(self.N, key=self.var_sort_key)
        
        cols_format = "r c r " + " ".join(["r"] * len(sorted_N))
        latex_str += f"$$\n\\begin{{array}}{{{cols_format}}}\n"
        
        def build_row(lhs, const_val, coeffs_dict, is_objective=False):
            all_zero_coeffs = all(coeffs_dict[j] == 0 for j in sorted_N)
            if const_val != 0 or all_zero_coeffs:
                const_str = to_latex_frac(const_val)
                has_printed = True
            else:
                const_str = ""
                has_printed = False
                
            row_str = f"{lhs} & = & {const_str}"
            
            for j in sorted_N:
                coef = coeffs_dict[j]
                if coef == 0:
                    row_str += " & " 
                else:
                    # Mũi tên biến vào CHỈ hiện trên hàm mục tiêu Z hoặc partial
                    if is_objective and j == entering:
                        var_j_str = f"\\overset{{\\downarrow}}{{{j}}}"
                    else:
                        var_j_str = j
                    
                    if not has_printed:
                        sign_str = "-" if coef < 0 else ""
                    else:
                        sign_str = "{}+" if coef > 0 else "{}-"
                    
                    abs_coef = abs(coef)
                    coef_str = "" if abs_coef == 1 else to_latex_frac(abs_coef)
                    
                    term_str = f"{sign_str} {coef_str}{var_j_str}"
                    row_str += f" & {term_str}"
                    has_printed = True
                    
            return row_str + " \\\\[1.5ex]\n"

        # 1. Hàm mục tiêu (Dùng Delta cong (partial) cho Pha 1)
        obj_name = "\\partial" if is_phase1 else "Z"
        latex_str += build_row(obj_name, self.v, self.c, is_objective=True)
        latex_str += "\\hline\n"
        
        # 2. Các ràng buộc
        sorted_B = sorted(self.B, key=self.var_sort_key)
        is_first_row = True
        
        for i in sorted_B:
            var_i_str = f"\\leftarrow {i}" if i == leaving else i
            
            # Thêm thanh chống vô hình rule{0pt}{3ex} vào dòng ngay dưới gạch ngang để không đè số
            if is_first_row:
                var_i_str = f"\\rule{{0pt}}{{3ex}}{var_i_str}"
                is_first_row = False
                
            coeffs_dict = {j: -self.A[i][j] for j in sorted_N}
            latex_str += build_row(var_i_str, self.b[i], coeffs_dict, is_objective=False)
            
        latex_str += "\\end{array}\n$$\n"
        self.steps_log.append(latex_str)

    def pivot(self, entering, leaving):
        A_rk = self.A[leaving][entering]
        new_b_leaving = self.b[leaving] / A_rk
        new_A_leaving = {}
        
        for j in self.N:
            if j == entering:
                new_A_leaving[leaving] = Fraction(1) / A_rk
            else:
                new_A_leaving[j] = self.A[leaving][j] / A_rk

        for i in self.B:
            if i == leaving: continue
            A_ik = self.A[i][entering]
            self.b[i] -= A_ik * new_b_leaving
            for j in self.N:
                if j == entering:
                    self.A[i][leaving] = -A_ik * new_A_leaving[leaving]
                else:
                    self.A[i][j] -= A_ik * new_A_leaving[j]
            del self.A[i][entering]

        c_k = self.c[entering]
        self.v += c_k * new_b_leaving
        for j in self.N:
            if j == entering:
                self.c[leaving] = -c_k * new_A_leaving[leaving]
            else:
                self.c[j] -= c_k * new_A_leaving[j]
        del self.c[entering]

        self.b[entering] = new_b_leaving
        self.A[entering] = new_A_leaving
        del self.b[leaving]
        del self.A[leaving]

        self.N.remove(entering)
        self.N.append(leaving)
        self.B.remove(leaving)
        self.B.append(entering)

    def is_twin_in_basis(self, j):
        if j.endswith("^+"):
            return j[:-2] + "^-" in self.B
        elif j.endswith("^-"):
            return j[:-2] + "^+" in self.B
        return False

    def solve(self):
        if self.method == "Two-Phase":
            orig_c = self.c.copy()
            orig_v = self.v
            
            # Xuất text Bài toán bổ trợ trước khi thay đổi dữ liệu
            self.log_auxiliary_problem()
            
            # Khởi tạo Pha 1
            self.N.append("x_0")
            for i in self.B:
                self.A[i]["x_0"] = Fraction(-1)
            
            self.c = {j: Fraction(0) for j in self.N}
            self.c["x_0"] = Fraction(1)
            self.v = Fraction(0)
            
            leaving = min(self.b, key=self.b.get)
            entering = "x_0"
            
            # Từ vựng xuất phát (Bước 3)
            self.log_dictionary("**Bước 3: Lập từ vựng xuất phát (Chưa khả thi):**", entering, leaving, is_phase1=True)
            self.pivot(entering, leaving)
            
            status = self._run_phase(rule="Dantzig", phase_name="Pha 1", is_phase1=True, start_iter=1)
            if status not in ["Optimal_Unique", "Optimal_Infinite"]: return status
            if self.v > 0: return "Infeasible"
            
            if "x_0" in self.B: return "Degenerate x_0"
            self.N.remove("x_0")
            for i in self.B: del self.A[i]["x_0"]
            
            self.v = orig_v
            self.c = {j: Fraction(0) for j in self.N}
            for j in orig_c:
                if j in self.N:
                    self.c[j] += orig_c[j]
                elif j in self.B:
                    self.v += orig_c[j] * self.b[j]
                    for k in self.N:
                        self.c[k] -= orig_c[j] * self.A[j][k]
                        
            # Dấu hiệu phân cách Pha 2
            self.steps_log.append("---\n### 🟢 Pha 2: Tối ưu bài toán gốc\n")
            return self._run_phase(rule="Dantzig", phase_name="Pha 2", is_phase1=False, start_iter=0)
            
        else:
            return self._run_phase(rule=self.method, phase_name="Bài toán", is_phase1=False, start_iter=0)

    def _run_phase(self, rule, phase_name, is_phase1, start_iter=0):
        iteration = start_iter
        while True:
            if all(val >= 0 for val in self.c.values()):
                if iteration == 0 and phase_name == "Bài toán":
                    title = "Từ vựng xuất phát (Đã tối ưu ngay từ đầu):"
                elif iteration == 0 and phase_name == "Pha 2":
                    title = "Từ vựng bắt đầu Pha 2 (Đã tối ưu):"
                else:
                    title = f"Từ vựng Tối ưu ({phase_name}):"
                self.log_dictionary(title, is_phase1=is_phase1)
                
                has_infinite = False
                for j in self.N:
                    if self.c[j] == 0 and not self.is_twin_in_basis(j):
                        has_infinite = True
                        break
                        
                return "Optimal_Infinite" if has_infinite else "Optimal_Unique"
                
            entering = None
            if rule == "Bland":
                candidates = [j for j in self.N if self.c[j] < 0]
                entering = min(candidates, key=self.var_sort_key) 
            else:
                entering = min(self.N, key=lambda j: self.c[j])

            leaving_candidates = []
            for i in self.B:
                if self.A[i][entering] > 0:
                    ratio = self.b[i] / self.A[i][entering]
                    leaving_candidates.append((ratio, i))
                    
            if not leaving_candidates:
                return "Unbounded"
                
            min_ratio = min(leaving_candidates, key=lambda x: x[0])[0]
            tied_leaving = [i for r, i in leaving_candidates if r == min_ratio]
            
            if rule == "Bland":
                leaving = min(tied_leaving, key=self.var_sort_key)
            else:
                leaving = tied_leaving[0]

            if phase_name == "Bài toán" and iteration == 0:
                title = "Từ vựng xuất phát:"
            elif phase_name == "Pha 1" and iteration == 1:
                title = "Từ vựng sau phép xoay ép buộc (Bắt đầu giải Pha 1):"
            elif phase_name == "Pha 2" and iteration == 0:
                title = "Từ vựng bắt đầu Pha 2 (Đã khôi phục hàm mục tiêu $Z$):"
            else:
                title = f"Từ vựng sau lần xoay {iteration} ({phase_name}):"

            self.log_dictionary(title, entering, leaving, is_phase1=is_phase1)
            self.pivot(entering, leaving)
            iteration += 1

# ==========================================
# GIAO DIỆN & TIỀN XỬ LÝ 
# ==========================================
def get_subscript(n):
    return str(n).translate(str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉"))

st.set_page_config(page_title="General LP Solver", layout="wide")
st.title("🧮 Trình giải Quy Hoạch Tuyến Tính Tổng Quát")
st.markdown("---")

st.sidebar.header("⚙️ Kích thước bài toán")
num_vars = st.sidebar.number_input("Số lượng biến (n):", 1, 10, 2)
num_constraints = st.sidebar.number_input("Số lượng ràng buộc (m):", 1, 10, 3)

st.subheader("1. Hàm mục tiêu (Objective Function)")
st.info("💡 **Dạng tổng quát:** $\\quad Z = c_1 x_1 + c_2 x_2 + \\dots + c_n x_n \\longrightarrow \\max / \\min$")
obj_type = st.radio("Mục tiêu của bài toán:", ["Max", "Min"], horizontal=True)

st.markdown("**👉 Nhập các hệ số $c_j$ tương ứng:**")
cols = st.columns(num_vars)
C_orig = []
for j in range(num_vars):
    with cols[j]:
        var_name = f"x{get_subscript(j+1)}"
        val = st.number_input(f"Hệ số của {var_name}", value=0.0, step=1.0, key=f"C_{j}")
        C_orig.append(Fraction(val))

st.subheader("2. Dấu của biến (Variable Conditions)")
cols = st.columns(num_vars)
var_signs = []
for j in range(num_vars):
    with cols[j]:
        var_name = f"x{get_subscript(j+1)}"
        sign = st.selectbox(var_name, ["≥ 0", "≤ 0", "Tùy ý"], key=f"vsign_{j}")
        var_signs.append(sign)

st.subheader("3. Các hệ ràng buộc (Constraints)")
st.info("💡 **Dạng tổng quát:** $\\quad a_{i1} x_1 + a_{i2} x_2 + \\dots + a_{in} x_n \\quad \\{\\le, \\ge, =\\} \\quad b_i$")

st.markdown("**👉 Nhập ma trận hệ số $a_{ij}$, chọn dấu và nhập giá trị vế phải $b_i$:**")
A_orig = []
B_orig = []
cons_signs = []

header_cols = st.columns(num_vars + 2)
for j in range(num_vars):
    header_cols[j].markdown(f"<div style='text-align: center; font-weight: bold;'>x{get_subscript(j+1)}</div>", unsafe_allow_html=True)
header_cols[num_vars].markdown("<div style='text-align: center; font-weight: bold;'>Dấu</div>", unsafe_allow_html=True)
header_cols[num_vars+1].markdown("<div style='text-align: center; font-weight: bold;'>b</div>", unsafe_allow_html=True)

for i in range(num_constraints):
    cols = st.columns(num_vars + 2)
    row = []
    for j in range(num_vars):
        with cols[j]:
            val = st.number_input(f"A_{i}_{j}", value=0.0, step=1.0, key=f"A_{i}_{j}", label_visibility="collapsed")
            row.append(Fraction(val))
    A_orig.append(row)
    
    with cols[num_vars]:
        sign = st.selectbox("Dấu", ["≤", "≥", "="], key=f"csign_{i}", label_visibility="collapsed")
        cons_signs.append(sign)
        
    with cols[num_vars+1]:
        val = st.number_input("b", value=0.0, step=1.0, key=f"B_{i}", label_visibility="collapsed")
        B_orig.append(Fraction(val))

st.markdown("---")
show_steps = st.checkbox("Hiển thị chi tiết quá trình xoay từ vựng", value=True)

if st.button("🚀 Giải Bài Toán", type="primary", use_container_width=True):
    std_c_list = []
    std_vars_map = [] 
    
    for j in range(num_vars):
        c_val = C_orig[j] if obj_type == "Min" else -C_orig[j]
        if var_signs[j] == "≥ 0":
            std_c_list.append(c_val)
            std_vars_map.append(f"x_{{{j+1}}}")
        elif var_signs[j] == "≤ 0":
            std_c_list.append(-c_val)
            std_vars_map.append(f"x'_{{{j+1}}}")
        elif var_signs[j] == "Tùy ý":
            std_c_list.extend([c_val, -c_val])
            std_vars_map.extend([f"x_{{{j+1}}}^+", f"x_{{{j+1}}}^-"])
            
    std_A_matrix = []
    std_b_list = []
    
    for i in range(num_constraints):
        row = []
        for j in range(num_vars):
            a_val = A_orig[i][j]
            if var_signs[j] == "≥ 0": row.append(a_val)
            elif var_signs[j] == "≤ 0": row.append(-a_val)
            elif var_signs[j] == "Tùy ý": row.extend([a_val, -a_val])
            
        if cons_signs[i] == "≤":
            std_A_matrix.append(row)
            std_b_list.append(B_orig[i])
        elif cons_signs[i] == "≥":
            std_A_matrix.append([-x for x in row])
            std_b_list.append(-B_orig[i])
        elif cons_signs[i] == "=":
            std_A_matrix.append(row)
            std_b_list.append(B_orig[i])
            std_A_matrix.append([-x for x in row])
            std_b_list.append(-B_orig[i])

    c_dict = {std_vars_map[j]: std_c_list[j] for j in range(len(std_vars_map))}
    b_dict = {}
    A_dict = {}
    
    slack_idx = 1
    for i in range(len(std_b_list)):
        slack_var = f"w_{{{slack_idx}}}"
        b_dict[slack_var] = std_b_list[i]
        A_dict[slack_var] = {std_vars_map[j]: std_A_matrix[i][j] for j in range(len(std_vars_map))}
        slack_idx += 1

    if show_steps:
        st.subheader("📝 Quá trình chuẩn hóa bài toán")
        
        obj_str = ""
        first = True
        for j, coef in c_dict.items():
            if coef != 0:
                obj_str += format_term_simple(coef, j, is_first=first)
                first = False
        if obj_str == "": obj_str = "0"
        
        st.markdown("**Bước 1: Đưa bài toán về dạng chuẩn (Hàm mục tiêu Min, biến không âm, các bất phương trình $\\le$)**")
        std_latex_1 = "$$\n\\begin{array}{r l}\n"
        std_latex_1 += f"\\min Z = & {obj_str} \\\\\n"
        std_latex_1 += "\\text{với các ràng buộc:} & \\\\\n"
        for i in range(len(std_b_list)):
            row_str = ""
            first = True
            for j, var_name in enumerate(std_vars_map):
                coef = std_A_matrix[i][j]
                if coef != 0:
                    row_str += format_term_simple(coef, var_name, is_first=first)
                    first = False
            
            if row_str == "": row_str = "0"
            std_latex_1 += f"& {row_str} \\le {to_latex_frac(std_b_list[i])} \\\\\n"
            
        var_chunks_1 = [std_vars_map[i:i + 8] for i in range(0, len(std_vars_map), 8)]
        for idx, chunk in enumerate(var_chunks_1):
            line = ", ".join(chunk)
            if idx == len(var_chunks_1) - 1:
                std_latex_1 += f"& {line} \\ge 0\n"
            else:
                std_latex_1 += f"& {line}, \\\\\n"
                
        std_latex_1 += "\\end{array}\n$$"
        st.markdown(std_latex_1)

        st.markdown("**Bước 2: Thêm các biến bù $w_i \\ge 0$ để chuyển bất phương trình thành hệ phương trình**")
        std_latex_2 = "$$\n\\begin{array}{r l}\n"
        std_latex_2 += f"\\min Z = & {obj_str} \\\\\n"
        std_latex_2 += "\\text{với các ràng buộc:} & \\\\\n"
        for i in range(len(std_b_list)):
            row_str = ""
            first = True
            for j, var_name in enumerate(std_vars_map):
                coef = std_A_matrix[i][j]
                if coef != 0:
                    row_str += format_term_simple(coef, var_name, is_first=first)
                    first = False
            
            slack_var = f"w_{{{i+1}}}"
            row_str += format_term_simple(Fraction(1), slack_var, is_first=first)
            
            if row_str == "": row_str = "0"
            std_latex_2 += f"& {row_str} = {to_latex_frac(std_b_list[i])} \\\\\n"
            
        all_vars = std_vars_map + [f"w_{{{i+1}}}" for i in range(len(std_b_list))]
        var_chunks_2 = [all_vars[i:i + 8] for i in range(0, len(all_vars), 8)]
        for idx, chunk in enumerate(var_chunks_2):
            line = ", ".join(chunk)
            if idx == len(var_chunks_2) - 1:
                std_latex_2 += f"& {line} \\ge 0\n"
            else:
                std_latex_2 += f"& {line}, \\\\\n"
                
        std_latex_2 += "\\end{array}\n$$"
        st.markdown(std_latex_2)

    min_b = min(b_dict.values())
    if min_b < 0:
        chosen_method = "Two-Phase"
        msg = "Hệ số $b_i$ của từ vựng xuất phát có chứa giá trị âm. Chương trình tự động áp dụng: **Phương pháp Đơn hình 2 Pha**."
    elif any(v == 0 for v in b_dict.values()):
        chosen_method = "Bland"
        msg = "Từ vựng xuất phát khả thi nhưng rơi vào trạng thái suy biến ($b_i = 0$). Chương trình tự động áp dụng: **Quy tắc Bland**."
    else:
        chosen_method = "Dantzig"
        msg = "Từ vựng xuất phát khả thi nghiêm ngặt ($b_i > 0$). Chương trình tự động áp dụng: **Quy tắc Dantzig**."

    st.success(msg)

    solver = SimplexDictionary(c_dict, A_dict, b_dict, Fraction(0), chosen_method)
    status = solver.solve()
    
    if show_steps:
        st.subheader("📜 Quá trình xoay Từ Vựng")
        for step in solver.steps_log:
            st.markdown(step)
            
    st.divider()
    
    if status in ["Optimal_Unique", "Optimal_Infinite"]:
        st.markdown("### ✅ Kết luận")
        
        if status == "Optimal_Unique":
            st.markdown("**Bài toán có nghiệm duy nhất.**")
        else:
            st.markdown("**Bài toán có vô số nghiệm.**")
        
        optimal_solution = []
        for j in range(num_vars):
            if var_signs[j] == "≥ 0":
                val = solver.b.get(f"x_{{{j+1}}}", Fraction(0))
            elif var_signs[j] == "≤ 0":
                val = -solver.b.get(f"x'_{{{j+1}}}", Fraction(0))
            elif var_signs[j] == "Tùy ý":
                val_plus = solver.b.get(f"x_{{{j+1}}}^+", Fraction(0))
                val_minus = solver.b.get(f"x_{{{j+1}}}^-", Fraction(0))
                val = val_plus - val_minus
            
            optimal_solution.append(f"x_{{{j+1}}} = {to_latex_frac(val)}")
        
        st.markdown("**Nghiệm tối ưu của bài toán là:**")
        sol_str = ", \\quad ".join(optimal_solution)
        st.markdown(f"$$ ( {sol_str} ) $$")
        
        final_obj = -solver.v if obj_type == "Max" else solver.v
        st.markdown("**Giá trị tối ưu của bài toán là:**")
        st.markdown(f"$$ Z = {to_latex_frac(final_obj)} $$")
        
    elif status == "Infeasible":
        st.markdown("### ❌ Kết luận")
        st.markdown("**Bài toán vô nghiệm.**")
    elif status == "Unbounded":
        st.markdown("### ⚠️ Kết luận")
        st.markdown("**Bài toán không giới nội.**")
