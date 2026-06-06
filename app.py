import streamlit as st
import pandas as pd
from fractions import Fraction

# ==========================================
# LÕI THUẬT TOÁN ĐƠN HÌNH (TỪ VỰNG - 2 PHA)
# ==========================================
class SimplexDictionary:
    def __init__(self, c, A, b, maximize=False):
        """
        Khởi tạo bài toán chuẩn Min: w = v + sum(c_j * x_j)
        Ràng buộc: x_i = b_i - sum(A_ij * x_j)
        """
        self.maximize = maximize
        self.num_vars = len(c)
        self.num_constraints = len(b)
        
        # Tập chỉ số
        self.N = [f"x{j+1}" for j in range(self.num_vars)]
        self.B = [f"x{self.num_vars + i + 1}" for i in range(self.num_constraints)]
        
        # Hệ số
        self.b = {self.B[i]: Fraction(b[i]) for i in range(self.num_constraints)}
        self.c = {self.N[j]: Fraction(-c[j]) if maximize else Fraction(c[j]) for j in range(self.num_vars)}
        self.A = {self.B[i]: {self.N[j]: Fraction(A[i][j]) for j in range(self.num_vars)} for i in range(self.num_constraints)}
        self.v = Fraction(0)
        
        self.steps_log = [] # Lưu trữ quá trình xoay

    def format_term(self, coef, var_name, is_first=False):
        """Format hệ số thành chuỗi toán học đẹp mắt"""
        if coef == 0: return ""
        sign = "+" if coef > 0 else "-"
        abs_coef = abs(coef)
        
        if is_first:
            sign_str = "-" if coef < 0 else ""
        else:
            sign_str = f" {sign} "
            
        coef_str = "" if abs_coef == 1 else str(abs_coef)
        return f"{sign_str}{coef_str}{var_name}"

    def log_dictionary(self, title="Từ vựng hiện tại:"):
        """Lưu lại từ vựng dưới định dạng LaTeX"""
        latex_str = f"**{title}**\n\n"
        # In các phương trình biến cơ sở
        for i in self.B:
            eq = f"$$ {i} = {self.b[i]} "
            for j in self.N:
                eq += self.format_term(-self.A[i][j], j)
            eq += " $$"
            latex_str += eq + "\n"
        
        # In hàm mục tiêu w
        obj = f"$$ w = {self.v} "
        for j in self.N:
            obj += self.format_term(self.c[j], j)
        obj += " $$"
        latex_str += obj + "\n"
        self.steps_log.append(latex_str)

    def pivot(self, entering, leaving):
        """Thực hiện xoay từ vựng"""
        # Phương trình của biến ra: x_r = b_r - sum(A_rj * x_j)
        # Rút x_k (entering) theo x_r (leaving)
        A_rk = self.A[leaving][entering]
        
        new_b_leaving = self.b[leaving] / A_rk
        new_A_leaving = {}
        for j in self.N:
            if j == entering:
                new_A_leaving[leaving] = Fraction(1) / A_rk
            else:
                new_A_leaving[j] = self.A[leaving][j] / A_rk

        # Thế vào các biến cơ sở còn lại
        for i in self.B:
            if i == leaving: continue
            A_ik = self.A[i][entering]
            self.b[i] = self.b[i] - A_ik * new_b_leaving
            for j in self.N:
                if j == entering:
                    self.A[i][leaving] = -A_ik * new_A_leaving[leaving]
                else:
                    self.A[i][j] = self.A[i][j] - A_ik * new_A_leaving[j]
            del self.A[i][entering]

        # Thế vào hàm mục tiêu
        c_k = self.c[entering]
        self.v = self.v + c_k * new_b_leaving
        for j in self.N:
            if j == entering:
                self.c[leaving] = -c_k * new_A_leaving[leaving]
            else:
                self.c[j] = self.c[j] - c_k * new_A_leaving[j]
        del self.c[entering]

        # Cập nhật từ vựng cho biến mới vào
        self.b[entering] = new_b_leaving
        self.A[entering] = new_A_leaving
        del self.b[leaving]
        del self.A[leaving]

        # Cập nhật tập chỉ số
        self.N.remove(entering)
        self.N.append(leaving)
        self.B.remove(leaving)
        self.B.append(entering)
        
        # Sắp xếp lại để hiển thị đẹp hơn
        self.N.sort(key=lambda x: int(x[1:]))
        self.B.sort(key=lambda x: int(x[1:]))

    def solve(self):
        # ---------------- PHA 1 ----------------
        min_b = min(self.b.values())
        if min_b < 0:
            self.log_dictionary("Từ vựng xuất phát (Chưa khả thi):")
            # Lưu lại hàm mục tiêu gốc
            orig_c = self.c.copy()
            orig_v = self.v
            
            # Thêm biến giả x0
            self.N.append("x0")
            for i in self.B:
                self.A[i]["x0"] = Fraction(-1)
            
            # Hàm mục tiêu Pha 1: w_aux = x0
            self.c = {j: Fraction(0) for j in self.N}
            self.c["x0"] = Fraction(1)
            self.v = Fraction(0)
            
            # Xoay ép buộc để lấy tính khả thi
            leaving = min(self.b, key=self.b.get)
            self.pivot("x0", leaving)
            self.log_dictionary(f"Sau phép xoay ép buộc (vào x0, ra {leaving}):")
            
            # Giải Pha 1
            status = self._run_simplex_phase()
            if status == "Unbounded": return "Lỗi: Pha 1 không giới hạn (Bất thường)"
            if self.v > 0: return "Bài toán vô nghiệm (Infeasible)."
            
            # Kết thúc Pha 1, xóa x0
            if "x0" in self.B:
                return "Bài toán suy biến phức tạp tại Pha 1 (Cần pivot x0 ra N)."
            self.N.remove("x0")
            for i in self.B: del self.A[i]["x0"]
            
            # Phục hồi hàm mục tiêu gốc
            self.v = orig_v
            self.c = {j: Fraction(0) for j in self.N}
            for j in orig_c:
                if j in self.N:
                    self.c[j] += orig_c[j]
                else: # j đang nằm trong cơ sở B
                    self.v += orig_c[j] * self.b[j]
                    for k in self.N:
                        self.c[k] -= orig_c[j] * self.A[j][k]
                        
            self.log_dictionary("Bắt đầu Pha 2 (Đã khôi phục hàm mục tiêu):")
        else:
            self.log_dictionary("Từ vựng xuất phát (Đã khả thi):")

        # ---------------- PHA 2 ----------------
        status = self._run_simplex_phase()
        if status == "Optimal":
            self.log_dictionary("Từ vựng Tối ưu:")
            return "Optimal"
        return status

    def _run_simplex_phase(self):
        iteration = 1
        while True:
            # Kiểm tra tối ưu (Tất cả c_j >= 0)
            if all(val >= 0 for val in self.c.values()):
                return "Optimal"
                
            # Chọn biến vào (Entering)
            # DANTZIG: Chọn c_j âm nhất
            # BLAND: Nếu có b_i == 0, ưu tiên chỉ số nhỏ nhất
            use_bland = any(val == 0 for val in self.b.values())
            
            entering = None
            if use_bland:
                # Chọn c_j < 0 có index nhỏ nhất
                candidates = [j for j in self.N if self.c[j] < 0]
                entering = min(candidates, key=lambda x: int(x[1:]))
            else:
                # Chọn c_j âm nhất
                entering = min(self.N, key=lambda j: self.c[j])

            # Chọn biến ra (Leaving)
            leaving_candidates = []
            for i in self.B:
                if self.A[i][entering] > 0:
                    ratio = self.b[i] / self.A[i][entering]
                    leaving_candidates.append((ratio, i))
                    
            if not leaving_candidates:
                return "Bài toán không giới hạn (Unbounded)."
                
            # Tìm min ratio
            min_ratio = min(leaving_candidates, key=lambda x: x[0])[0]
            tied_leaving = [i for r, i in leaving_candidates if r == min_ratio]
            
            # Dùng Bland cho biến ra nếu có tie hoặc đang dùng Bland
            leaving = min(tied_leaving, key=lambda x: int(x[1:]))

            self.steps_log.append(f"**Xoay lần {iteration}:** Cho `{entering}` vào, `{leaving}` ra.")
            self.pivot(entering, leaving)
            self.log_dictionary(f"Sau lần xoay {iteration}:")
            iteration += 1


# ==========================================
# GIAO DIỆN NGƯỜI DÙNG (STREAMLIT)
# ==========================================
st.set_page_config(page_title="LP Solver - Dictionary Method", layout="wide")

st.title("🧮 Trình giải Quy Hoạch Tuyến Tính Tổng Quát")
st.markdown("Giải thuật **Đơn hình Từ vựng 2 Pha** (Kết hợp Dantzig & Bland). Hỗ trợ xuất chi tiết các bước xoay.")

# --- Cài đặt kích thước bài toán ---
col1, col2 = st.columns(2)
with col1:
    num_vars = st.number_input("Số lượng biến số (n):", min_value=1, max_value=10, value=2)
with col2:
    num_constraints = st.number_input("Số lượng ràng buộc (m):", min_value=1, max_value=10, value=3)

# --- Nhập Hàm mục tiêu ---
st.subheader("1. Hàm mục tiêu")
obj_type = st.radio("Loại bài toán:", ["Max", "Min"], horizontal=True)

st.write("Nhập hệ số của hàm mục tiêu (c1, c2, ...):")
obj_cols = st.columns(num_vars)
c = []
for j in range(num_vars):
    with obj_cols[j]:
        val = st.number_input(f"c{j+1}", value=0.0, step=1.0, key=f"obj_{j}")
        c.append(val)

# --- Nhập Ràng buộc ---
st.subheader("2. Ràng buộc")
st.write("Nhập hệ số ma trận A, dấu ràng buộc và cột b:")

A = []
b = []
signs = []

for i in range(num_constraints):
    cols = st.columns(num_vars + 2)
    row_A = []
    for j in range(num_vars):
        with cols[j]:
            val = st.number_input(f"x{j+1}", value=0.0, step=1.0, key=f"A_{i}_{j}", label_visibility="collapsed")
            row_A.append(val)
    A.append(row_A)
    
    with cols[num_vars]:
        sign = st.selectbox("Dấu", ["<=", ">=", "="], key=f"sign_{i}", label_visibility="collapsed")
        signs.append(sign)
        
    with cols[num_vars + 1]:
        val_b = st.number_input("b", value=0.0, step=1.0, key=f"b_{i}", label_visibility="collapsed")
        b.append(val_b)

# --- Tiền xử lý ẩn ---
# Để đơn giản hóa logic giao diện, tự động thêm slack/surplus và đưa về '=' trước khi ném vào Solver
std_A = []
std_b = []
std_c = list(c)

# Bù thêm biến cho các ràng buộc <= và >=
slack_count = 0
for i in range(num_constraints):
    row = A[i].copy()
    if signs[i] == "<=":
        slack_count += 1
    elif signs[i] == ">=":
        slack_count += 1

# Cập nhật hàm mục tiêu (thêm số 0 cho các biến bù)
std_c.extend([0] * slack_count)

current_slack = 0
for i in range(num_constraints):
    row = A[i].copy()
    # Mở rộng dòng để chứa các biến bù
    row.extend([0] * slack_count)
    
    if signs[i] == "<=":
        row[num_vars + current_slack] = 1
        current_slack += 1
    elif signs[i] == ">=":
        row[num_vars + current_slack] = -1
        current_slack += 1
        
    # Nếu hệ số b âm, đổi dấu toàn bộ phương trình để b >= 0 chuẩn bị cho lập từ vựng
    if b[i] < 0 and signs[i] == "=": # Với =, đổi dấu thoải mái
        row = [-x for x in row]
        std_b.append(-b[i])
    else:
        std_b.append(b[i])
    std_A.append(row)

# --- Tùy chọn hiển thị & Nút Giải ---
st.subheader("3. Tùy chọn & Giải")
show_steps = st.checkbox("Hiển thị chi tiết quá trình xoay từ vựng", value=True)

if st.button("🚀 Giải Bài Toán", type="primary"):
    # Khởi tạo thuật toán
    is_max = (obj_type == "Max")
    solver = SimplexDictionary(std_c, std_A, std_b, maximize=is_max)
    
    with st.spinner("Đang xử lý thuật toán..."):
        status = solver.solve()
    
    st.divider()
    
    # KẾT QUẢ CUỐI CÙNG
    if status == "Optimal":
        st.success("✅ Đã tìm thấy nghiệm tối ưu!")
        final_z = -solver.v if is_max else solver.v
        st.markdown(f"### Giá trị tối ưu: $Z = {final_z}$")
        
        st.markdown("**Nghiệm của các biến:**")
        cols = st.columns(num_vars)
        for j in range(num_vars):
            var_name = f"x{j+1}"
            # Nếu biến nằm trong cơ sở thì lấy giá trị từ b, ngược lại là 0
            val = solver.b.get(var_name, 0)
            with cols[j]:
                st.info(f"${var_name} = {val}$")
                
    else:
        st.error(f"❌ Thuật toán dừng lại. Trạng thái: {status}")

    # XUẤT CHI TIẾT QUÁ TRÌNH
    if show_steps and solver.steps_log:
        st.subheader("📜 Chi tiết quá trình xoay Từ Vựng")
        for step in solver.steps_log:
            st.markdown(step)
            
st.caption("Chương trình sử dụng phân số (`fractions`) để loại bỏ sai số thập phân, đảm bảo xuất ra đúng chuẩn giáo trình QHTT.")
